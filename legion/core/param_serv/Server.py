#!/usr/bin/env python2
from __future__ import print_function, with_statement, division, generators, absolute_import
""" Extremely simple launch script. Should be improved. """

import os, sys, time, random, threading, socket, re
import textwrap
import subprocess as sp
from traceback import format_exc

from legion.core.param_serv.param_utils import *
from legion.core.param_serv.AcceptorThread import AcceptorThread


def format_script(text):
    return bcolors.OKGREEN + insert_tabs("\n".join(textwrap.wrap(text, 60))) + bcolors.ENDC

def generate_qsub_msub_launch_script(allocation_name, key_value_exports, executable, user_script_args,
                                     walltime, job_name, pydev, instances, user_script_path):
    return textwrap.dedent(
            """
            #PBS -A {allocation_name}
            #PBS -l walltime={walltime}
            #PBS -l nodes=1:gpus=1
            #PBS -N {job_name}
            #PBS -t 1-{instances}

            {key_value_exports}
            export PYTHONPATH="$PYTHONPATH":"{pydev}"

            export THEANO_FLAGS="device={theano_device_type},floatX=float32"
            {executable} '{script_path}' {user_args}

            wait
            echo "qsub/msub script done"
            """) \
            .format(
                    allocation_name=    allocation_name,
                    key_value_exports=  key_value_exports,
                    executable=         executable,
                    user_args=          user_script_args,
                    walltime=           walltime,
                    job_name=           job_name,
                    pydev=              pydev,
                    instances=          instances,
                    script_path=        user_script_path,
                    theano_device_type= "gpu0"
                    )

class Server(object):
    def __init__(self, instances):
        self.acceptor = self.launch_server(instances)

    def stop(self):
        if self.acceptor is not None:
            self.acceptor.stop()
            self.acceptor.exit()
            self.acceptor.join()

    def join_threads(self):
        if self.acceptor is not None:
            self.acceptor.join_threads()
            self.acceptor.join()

    def launch_server(self, instances):
        """ This launches the server acceptor thread. """
        db = {}
        db_rlock = threading.RLock()
        meta = {}
        meta_rlock = threading.RLock()

        acceptor = AcceptorThread(
                        instances=   instances,
                        meta=        meta,
                        meta_rlock=  meta_rlock,
                        db=          db,
                        db_rlock=    db_rlock,
                        )
        acceptor.setDaemon(True)
        self.port = acceptor.bind()
        acceptor.start()

        return acceptor

    def launch_clients(
                       self,
                       user_script_path,
                       job_name,
                       instances,
                       walltime="12:00:00",
                       allocation_name="",
                       user_script_args="",
                       debug=False,
                       debug_pycharm=False,
                       force_jobdispatch=False,
                       debug_specify_devices=None
                       ):
        """ This makes the call to jobdispatch, msub or qsub.
         This function never ruturns! """
        ###################################################################
        # Function argument/param consistency check
        # TODO: This needs to be fairly tight at "shipping"
        ###################################################################
        assert os.path.exists(user_script_path), "Could not find the user script with path %s" % user_script_path
        assert debug or allocation_name is not None, "If we aren't debugging, we need an allocation name"

        if instances is None and debug:
            instances = 1

        assert instances is not None, "The parameter 'instances' needs to be specified."
        assert isinstance(instances, int), "The parameter 'instances' needs to be an int."

        executable = "python2"
        pydev = ""

        ###################################################################
        # Setup of the Pycharm remote debugging
        ###################################################################
        if debug_pycharm and debug:
            try:
                # Add the standard OSX paths for pydevd
                to_add = [
                          "/Applications/PyCharm.app/Contents/helpers/pydev",
                          "/Applications/PyCharm CE.app/Contents/helpers/pydev",
                          ]

                for path in to_add:
                    if os.path.exists(path):
                        sys.path.append(path)

                import pydevd
                import re
                # not tight. there could be more then one debugging server open
                debug_procs = os.popen("ps -A | grep pydevd | grep -v grep").read().split("\n")
                pwh(debug_procs)
                debugger_is_running = debug_procs[0] != ''

                if debugger_is_running:
                    # extract the port of the debug server
                    print("< app found a debugger >")
                    res = debug_procs[0] # there could be more than one. eventually, we could use this if we need to
                    port = re.findall("--port \w+", res)[0].split()[1]
                    print("trying port {port}".format(port=port))
                    pydev = '/Applications/PyCharm CE.app/Contents/helpers/pydev/'

                    # change the executable
                    executable = "python2 -m pydevd --multiproc --client 127.0.0.1 --port {port} --file "\
                                 .format(port=port)

            except ImportError:
                pwh("You need to have the pydevd script in your path in order to use remote debugging.")
                pwh(format_exc())

        ######################################################################
        # Add some exports for the information that the legion client needs
        ######################################################################
        to_export = {
                     "legion_walltime":    walltime,
                     "legion_job_name":    job_name,
                     "legion_instances":   instances,
                     "legion_script_path": user_script_path,
                     "legion_server_ip":   our_ip(),
                     "legion_server_port": self.port,
                     "legion_debug":       str(debug).lower(),
                     }

        exports_substring_generator = ("export {key}=\"{val}\"".format(key=key, val=val)
                                       for key, val in to_export.iteritems())
        key_value_exports = " ".join(exports_substring_generator) + " "

        # if dnsdomainname fails, "" is assigned to dnsdomainname.
        try:
            dnsdomainname = re.sub("\s", "", os.popen("dnsdomainname 2>/dev/null").read())
        except:
            # We don't really care why we failed.
            dnsdomainname = None

        ################################################################################
        # This part is very important.
        # This is the dnsnames that we associate with each launch utility.
        ################################################################################

        qsub_set = {"guillimin.clumeq.ca"}
        msub_set = {"helios"}  # add "helios" in this field to use msub on helios

        launch_info_msub_qsub_jobdispatch = textwrap.dedent(
            """We queued the jobs onto the cluster. It might take up to a few hours for them to get executed.
            Enter the command 'showq -u $USER' to see their state.
            Enter 'canceljob XXX' to cancel a serie of jobs, where XXX is the job number that you can see in showq.
            If you queue more than one job at once, the job number will have this format:
            \tXXX[YY]
            This means that the job XXX has YY sub jobs. You can cancel them all at once by entering the command
            \tcanceljob XXX
            """)

        launch_info_debug = "Launching legion locally.\nPressing ctrl+C will stop the whole thing."

    #################################################################################
    # Here are the launch scripts specific to msub, qsub and jobdispatch.
    #################################################################################
        processes = []
        print("\n\n" + bcolors.BOLD + "Legion:" + bcolors.ENDC)
        if debug:
            assert debug_specify_devices is None or len(debug_specify_devices) == instances, "if debug_specify_devices is specified, its size needs to be equal to the instances param"

            print(">>> local debug mode")
            print(launch_info_debug)
            print("\nScripts being executed by the subprocess(es) as means of local debugging:\n")

            for i in xrange(instances):
                device = "cpu" if debug_specify_devices is None else debug_specify_devices[i]
                launch_code = """export THEANO_FLAGS="device={theano_device_type},floatX=float32"
                      {executable} '{script_path}' {user_args}""".format(
                                                                   theano_device_type=  device,
                                                                   executable=          executable,
                                                                   script_path=         user_script_path,
                                                                   user_args=           user_script_args
                                                                   )

                complete_code = key_value_exports + launch_code
                print(format_script(complete_code))
                print("\n")
                process = sp.Popen("sh", stdin=sp.PIPE, stdout=sys.stdout)
                process.communicate(complete_code)[0]
                processes.append(process)

        elif not force_jobdispatch and (dnsdomainname in qsub_set or dnsdomainname in msub_set):
            ########################
            # msub or qsub
            ########################

            # We are either using qsub or msub. Not using ternary conditional operator for clarity.
            if dnsdomainname in qsub_set:
                program = "qsub"
            else:
                program = "msub"

            print("\n>>> %s" % program)
            print(launch_info_msub_qsub_jobdispatch)
            print("'%s' script being run by the cluster:" % program)
            launch_script = generate_qsub_msub_launch_script(allocation_name, key_value_exports, executable, user_script_args,
                                             walltime, job_name, pydev, instances, user_script_path)
            print(format_script(launch_script))

            process = sp.Popen(program, stdin=sp.PIPE, stdout=sys.stdout)
            # pass the code through stdin
            process.communicate(launch_script)[0]
            processes.append(process)

        else:
            ########################
            # Jobdispatch
            ########################

            print(">>> jobdispatch")
            print(launch_info_msub_qsub_jobdispatch)
            print("\n'jobdispatch' script being run by the cluster:")

            to_export = {
                     "legion_walltime":    walltime,
                     "legion_job_name":    job_name,
                     "legion_instances":   instances,
                     "legion_script_path": user_script_path,
                     "legion_server_ip":   our_ip(),
                     "legion_server_port": self.port,
                     "legion_debug":       str(debug).lower(),
                     "THEANO_FLAGS":       "device=gpu0,floatX=float32",
                     }

            exports_substring_generator = ("--env={key}=\"{val}\"".format(key=key, val=val)
                                           for key, val in to_export.iteritems())
            key_value_exports = " ".join(exports_substring_generator) + " "
            execution = "python2 \"{user_script_path}\" {user_args}"\
                .format(
                        user_script_path=user_script_path,
                        user_args=user_script_args)
            jobdispatch_cmd = "jobdispatch --gpu --repeat_jobs={instances} {exports} {execution}" \
                .format(exports=key_value_exports, execution=execution, instances=instances)

            print(format_script(jobdispatch_cmd))

            process = sp.Popen(jobdispatch_cmd, shell=True, stderr=sys.stdout, stdout=sys.stdout)
            processes.append(process)

        ################################################################################
        # End of the main thread. We sleep here until the user kills us.
        # Other approaches have been too unreliable; this one is simple and has yet to fail
        # having the expected behavior.
        ################################################################################
        try:
            while True:
                    time.sleep(1000000)
        except KeyboardInterrupt:
            print("\nReceived KeyboardInterrupt. Exiting.")
            exit(0)

        print("Exiting.")
