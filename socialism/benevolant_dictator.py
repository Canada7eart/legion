#!/usr/bin/env python2
from __future__ import print_function, with_statement, division, generators, absolute_import
""" Extremely simple launch script. Should be improved. """

import os, sys, time, random, threading, socket
import subprocess as sp
from traceback import format_exc

from socialism.param_serv.param_utils import *
import socialism.param_serv.server

import cython

class _Server(object):
    def __init__(self):
        self.launch_server()

    def launch_server(self):
        """ This launches the server acceptor thread. """
        db = {}
        db_rlock = threading.RLock()
        meta = {}
        meta_rlock = threading.RLock()

        acceptor = socialism.param_serv.server.AcceptorThread(
                        meta=        meta,
                        meta_rlock=  meta_rlock,
                        db=          db,
                        db_rlock=    db_rlock,
                        )

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
        debug_specify_device="gpu0",
    ):
        """ This makes the call to jobdispatch, msub or qsub """

        ###################################################################
        # Function argument/param consistency check
        # TODO: This needs to be fairly tight at "shipping"
        ###################################################################
        assert os.path.exists(user_script_path), "Could not find the user script with path %s" % user_script_path
        assert debug or allocation_name is not None, "If we aren't debugging, we need an allocation name"

        executable = "python2"
        pydev = ""

        ###################################################################
        # Setup of the Pycharm remote debugging
        ###################################################################
        if debug_pycharm and debug:
            try:
                # Add the standard OSX paths for pydevd
                to_add = ["/Applications/PyCharm.app/Contents/helpers/pydev",
                          "/Applications/PyCharm CE.app/Contents/helpers/pydev"]

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

        # Add some exports that we need in the client
        to_export = {
            "SOCIALISM_walltime":         walltime,
            "SOCIALISM_job_name":         job_name,
            "SOCIALISM_instances":        instances,
            "SOCIALISM_script_path":      user_script_path,
            "SOCIALISM_server_ip":        our_ip(),
            "SOCIALISM_server_port":      self.port,
            "SOCIALISM_debug":            str(debug).lower(),
            }

        exports_substring_generator = ("export {key}=\"{val}\"".format(key=key, val=val)
                                       for key, val in to_export.iteritems())

        key_value_exports = " ".join(exports_substring_generator) + " "

        ########################################################################
        # This will eventually be useless, as we will be only using jobdispatch
        ########################################################################
        qsub_msub_or_debug_launch_template = \
            """
            #PBS -A {allocation_name}
            #PBS -l walltime={walltime}
            #PBS -l nodes=1:gpus=1
            #PBS -N {job_name}
            #PBS -t 1-{instances}

            {key_value_exports}
            export PYTHONPATH="$PYTHONPATH":"{pydev}"

            export THEANO_FLAGS="device={theano_device_type}0,floatX=float32"
            {executable} '{script_path}' {user_args}

            wait
            echo "qsub/msub script done"
            """ \
            .format(
                allocation_name=       allocation_name,
                key_value_exports=     key_value_exports,
                executable=            executable,
                user_args=             user_script_args,
                walltime=              walltime,
                job_name=              job_name,
                pydev=                 pydev,
                instances=             instances,
                script_path=           user_script_path,
                theano_device_type=    "gpu0" if not debug else debug_specify_device,
                )

        # This is basic logic to detect if we are on Guillimin. We also previously used it to detect Helios

        import re
        # if dnsdomainname fails, "" is assigned to dnsdomainname.
        try:
            dnsdomainname = re.sub("\s", "", os.popen("dnsdomainname 2>/dev/null").read())
        except:
            # We don't really care why we failed.
            dnsdomainname = None

        qsub_set = {"guillimin.clumeq.ca"}
        msub_set = {"helios"}  # used to be for msub

        if debug:
            print(">>> debug")
            # Add some fake qsub env variables to emulate those that would be present at the time of execution
            to_export = {"PBS_NODENUM": "0"}

            env_code = "\n".join(("export {key}={value}".format(key=key, value=value)
                                  for key, value in to_export.items())) + "\n"

            complete_code = key_value_exports + env_code + "sh" + qsub_msub_or_debug_launch_template

            process = sp.Popen("sh", shell=True, stdin=sp.PIPE, stdout=sys.stdout)
            process.communicate(complete_code)[0]

        # allow further customization then just command name
        elif not force_jobdispatch and dnsdomainname in qsub_set:
            print(">>> qsub")
            process = sp.Popen("qsub", shell=True, stdin=sp.PIPE, stdout=sys.stdout)
            # pass the code through stdin
            process.communicate(qsub_msub_or_debug_launch_template)[0]

        # allow further customization then just command name
        elif not force_jobdispatch and dnsdomainname in msub_set:
            print(">>> msub")
            process = sp.Popen("msub", shell=True, stdin=sp.PIPE, stdout=sys.stdout)
            # pass the code through stdin
            print(qsub_msub_or_debug_launch_template)
            process.communicate(qsub_msub_or_debug_launch_template)[0]

        # fall back on jobdispatch
        else:
            assert False, "support for jobdispatch is not yet available"
            print(">>> jobdispatch")
            ###################################################################
            # Generation of the launch script
            # as jobdispatch cannot read the script with stdin
            ###################################################################

            execution = "python2 \"{user_script_path}\" {user_args}"\
                .format(theano_flags=theano_flags,
                        user_script_path=user_script_path,
                        user_args=user_script_args)

            ###################################################################
            # We make and run the jobdispatch shell line
            ###################################################################

            experimental_jobdispatch_cmd = "jobdispatch --gpu --raw='{exports}' {execution}" \
                .format(exports=key_value_exports, execution=execution)

            print(experimental_jobdispatch_cmd)
            jobdispatch_proc = sp.Popen(experimental_jobdispatch_cmd, shell=True, stdin=sp.PIPE, stdout=sys.stdout)
            ret_val_jobdispatch_proc = jobdispatch_proc.wait()

        print("benevolent_dictator - done")

try:
    Server = cython.inline("_Server")["_Server"]
except:
    Server = _Server
