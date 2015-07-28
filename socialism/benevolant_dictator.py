#!/usr/bin/env python2
from __future__ import print_function, with_statement, division, generators

""" Extremely simple launch script. Should be improved. """
import os, sys, re, threading, socket, time
import subprocess as sp
import socialism.param_serv.server
import random
import re

from param_serv.param_utils import *

from subprocess import *
from traceback import format_exc

class Server(object):
    def __init__(self):
        pass

    def _launch_server(self):
        db = {}
        db_rlock = threading.RLock()
        meta = {}
        meta_rlock = threading.RLock()

        acceptor = socialism.param_serv.server.AcceptorThread(
            meta=meta,
            meta_rlock=meta_rlock,
            db=db,
            db_rlock=db_rlock,
            )

        self.port = acceptor.bind()
        acceptor.start()
        return acceptor

    def _launch_multiple(
        self,
        user_script_path,
        project_name,
        walltime,
        number_of_nodes,
        number_of_gpus,
        job_name,
        task_name,
        procs_per_job,
        lower_bound,
        upper_bound,
        theano_flags,
        user_script_args="",
        debug=False,
        debug_pycharm=False,
        force_jobdispatch=False,

    ):

        # There variables will be changed if Pycharm remote debugging is enabled,
        # as the remote debugger needs to be the one running the script
        executable = "python2"
        pydev = ""

        ###################################################################
        # Function argument/param consistency check
        # TODO: This needs to be tight at "shipping"
        ###################################################################
        assert procs_per_job >= 1, "There needs to be at least one process per job."

        ###################################################################
        # Setup of the Pycharm remote debugging
        ###################################################################
        if debug_pycharm:
            # find the debugging process
            sys.path.append("/Applications/PyCharm CE.app/Contents/helpers/pydev/")
            import pydevd
            import re
            debug_procs = os.popen("ps -A | grep pydevd | grep -v grep").read().split("\n")
            debugger_is_running = debug_procs[0] != ''

            if debugger_is_running:
                # extract the port of the debug server
                print("< app found a debugger >")
                res = debug_procs[0] # there could be more than one. eventually, we could use this if we need to
                port = re.findall("--port \w+", res)[0].split()[1]
                print("trying port {port}".format(port=port))
                pydev = '/Applications/PyCharm CE.app/Contents/helpers/pydev/'

                # change the executable
                executable = "python2 -m pydevd --multiproc --client 127.0.0.1 --port {port} --file ".format(port=port)

        qsub_msub_or_debug_launch_template = \
            """
            #PBS -A {project_name}
            #PBS -l walltime={walltime}
            #PBS -l nodes={number_of_nodes}:gpus={number_of_gpus}
            #PBS -r n
            #PBS -N {job_name}

            export PYTHONPATH="$PYTHONPATH":"{pydev}"
            export THEANO_FLAGS="{theano_flags}"

            for i in $(seq 0 $(expr {procs_per_job} - 1))
            do
                echo "starting job $i"
                {executable} '{script_path}' '{user_args}' &
            done
            wait
            echo "qsub like script done"
            """ \
            .format(
                executable=       executable,
                user_args=        user_script_args,
                project_name=     project_name,
                walltime=         walltime,
                number_of_nodes=  number_of_nodes,
                number_of_gpus=   number_of_gpus,
                job_name=         job_name,
                pydev=            pydev,
                procs_per_job=    procs_per_job,
                script_path=      user_script_path,
                theano_flags=     theano_flags,
                )

        # This is basic logic to detect if we are on either Helios or Guillimin
        try:
            import re
            dnsdomainname = re.sub("\s", "", os.popen("dnsdomainname").read())
        except NameError:
            print("dnsdomainname: NameError")
            dnsdomainname = None
            print(format_exc())


        qsub_set = {"guillimin.clumeq.ca"}
        msub_set = {"helios"}

        print("\ndnsdomainname: {dnsdomainname}".format(dnsdomainname=dnsdomainname))
        print("debug_pycharm: {debug_pycharm}".format(debug_pycharm=debug_pycharm))
        print("force_jobdispatch: {force_jobdispatch}".format(force_jobdispatch=force_jobdispatch))

        exit(0)

        if debug:

            print(">>> qsub")
            # Add some fake qsub env variables to emulate those that would be present at the time of execution
            to_export = {
                "PBS_NODENUM": "0",
                }

            env_code = "\n".join(["export {key}={value};".format(key=key, value=value)
                for key, value in to_export.items()]) + "\n"

            complete_code = env_code + "sh" + qsub_msub_or_debug_launch_template

            # run the script
            process = sp.Popen("sh --debug", shell=True, stdin=sp.PIPE, stdout=sys.stdout)
            stdout = process.communicate(complete_code)[0]

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
            process.communicate(qsub_msub_or_debug_launch_template)[0]

        # fall back on jobdispatch
        else:
            print(">>> jobdispatch")
            ###################################################################
            # Generation of the launch script
            # as jobdispatch cannot read the script with stdin
            ###################################################################

            # Add some exports that we need in the client
            to_export = {
                "SOCIALISM_project_name":     project_name,
                "SOCIALISM_walltime":         str(walltime),
                "SOCIALISM_number_of_nodes":  str(number_of_nodes),
                "SOCIALISM_number_of_gpus":   str(number_of_gpus),
                "SOCIALISM_job_name":         job_name,
                "SOCIALISM_task_name":        task_name,
                "SOCIALISM_procs_per_job":    str(procs_per_job),
                "SOCIALISM_script_path":      user_script_path,
                "SOCIALISM_server_ip":        our_ip(),
                "SOCIALISM_server_port":      str(self.port),
                "SOCIALISM_debug":            str(debug).lower(),
                }
            standard_shebang =    "#! /usr/bin/env bash\n"
            key_value_exports =   ";\n".join(["export {export_key}=\"{export_value}\""
                                      .format(export_key=key, export_value=value) for key, value in to_export.iteritems()])
            execution =           ";\nTHEANO_FLAGS=\"{theano_flags}\" python2 \"/home/julesgm/task/user_script.py\" {user_args};".format(theano_flags=theano_flags, user_args=user_script_args)
            complete = standard_shebang + key_value_exports + execution

            # We generate a random name so multiple servers on the same machine don't overlap
            while True:
                file_name = "tmp_{rand_id}.sh".format(rand_id=random.randint(0, 10000000))
                path_to_tmp = os.path.join(os.path.dirname(__file__), file_name)
                if not os.path.exists(path_to_tmp):
                    break

            # Save the script
            with open(path_to_tmp, "w") as tmp:
                tmp.write(complete)

            # Make it executable
            chmod_x_cmd = "chmod +x \"{path}\"".format(path=path_to_tmp)
            sp.Popen(chmod_x_cmd, shell=True).wait()

            # jobdispatch needs this with guillimin
            if dnsdomainname == "guillimin.clumeq.ca":
                os.environ["JOBDISPATCH_GPU_PARAM"] = "--gpu"

            ###################################################################
            # We make and run the jobdispatch shell line
            ###################################################################
            jobdispatch_cmd = "jobdispatch --gpu --duree={walltime} \"{cmd}\"" \
                                 .format(
                                     path=        user_script_path,
                                     walltime=    walltime,
                                     cmd=         path_to_tmp,
                                     )

            sp.Popen(jobdispatch_cmd, shell=True, stdin=sp.PIPE, stdout=sys.stdout).wait()

        print("benevolent_dictator - done")