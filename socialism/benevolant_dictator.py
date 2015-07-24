#!/usr/bin/env python2
from __future__ import print_function, with_statement, division, generators

""" Extremely simple launch script. Should be improved. """
import os, sys, re, threading, socket, time
import subprocess as sp
import param_serv.server
import random

from param_serv.param_utils import *
from dbi_utils import search_file
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

        acceptor = param_serv.server.AcceptorThread(
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
        script_path,
        project_name,
        walltime,
        number_of_nodes,
        number_of_gpus,
        job_name,
        task_name,
        procs_per_job,
        lower_bound,
        upper_bound,
        user_args="",
        debug=False,
        debug_pycharm=False,
        force_jobdispatch=False,
    ):

###################################################################
# Grunt Work
###################################################################
        pydev = ""
        executable = "python2"

        ############
        # function argument/param consistency check; this is a directly user exposed function.
        # TODO: this, tightly, when we have consistent basic functionality
        ############
        assert procs_per_job >= 1, "There needs to be at least one process per job."

        ############
        # These environment variables are going to be used by the clients
        ############

        to_export = {
            "SOCIALISM_project_name":     project_name,
            "SOCIALISM_walltime":         str(walltime),
            "SOCIALISM_number_of_nodes":  str(number_of_nodes),
            "SOCIALISM_number_of_gpus":   str(number_of_gpus),
            "SOCIALISM_job_name":         job_name,
            "SOCIALISM_task_name":        task_name,
            "SOCIALISM_procs_per_job":    str(procs_per_job),
            "SOCIALISM_script_path":      script_path,
            "SOCIALISM_server_ip":        our_ip(),
            "SOCIALISM_server_port":      str(self.port),
            "SOCIALISM_debug":            str(debug).lower(),
            }

###################################################################
# Pycharm remote debugging
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
        launch_template = \
            """
            #PBS -A {project_name}
            #PBS -l walltime={walltime}
            #PBS -l nodes={number_of_nodes}:gpus={number_of_gpus}
            #PBS -r n
            #PBS -N {job_name}

            export PYTHONPATH="$PYTHONPATH":"{pydev}"

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
            user_args=        user_args,
            project_name=     project_name,
            walltime=         walltime,
            number_of_nodes=  number_of_nodes,
            number_of_gpus=   number_of_gpus,
            job_name=         job_name,
            pydev=            pydev,
            procs_per_job=    procs_per_job,
            script_path=      script_path,
            )


        dnsdomainname = os.popen("dnsdomainname").read()

        qsub_set = {"guillimin.clumeq.ca"}
        msub_set = {"helios"}

        if debug:
            env = {
                "PBS_NODENUM": "0",
                }

            # add some fake qsub env variables to emulate those that would be present at the time of execution
            env_code = "\n".join(["export {key}={value};".format(key=key, value=value) for key, value in env.items()]) + "\n"
            complete_code = env_code + "sh" + launch_template

            # run the script
            process = sp.Popen("sh --debug", shell=True, stdin=sp.PIPE, stdout=sys.stdout)
            stdout = process.communicate(complete_code)[0]

        # allow further customization then just command name
        elif not force_jobdispatch and  dnsdomainname in qsub_set:
            print(">>> qsub")
            process = sp.Popen("qsub", shell=True, stdin=sp.PIPE, stdout=sys.stdout)
            # pass the code through stdin
            process.communicate(launch_template)[0]

        # allow further customization then just command name
        elif not force_jobdispatch and dnsdomainname in msub_set:
            print(">>> msub")
            process = sp.Popen("msub", shell=True, stdin=sp.PIPE, stdout=sys.stdout)
            # pass the code through stdin
            process.communicate(launch_template)[0]

        # fall back on jobdispatch
        else:
            print(">>> jobdispatch")

            ###################################################################
            # Generation of the launch script
            # as jobdispatch cannot read the script with stdin
            ###################################################################
            generic_shebang =    "#! /usr/bin/env bash\n"
            key_value_exports =  ";\n".join(["export {key}=\"{value}\"".format(key=key, value=value) for key, value in to_export.iteritems()])
            execution =          ";\npython2 \"/home/julesgm/task/user_script.py\";"

            complete = generic_shebang + key_value_exports + execution

            # we generate a random name so multiple servers on the same machine don't overlap
            while True:
                file_name = "tmp_{rand_id}.sh".format(rand_id=random.randint(0, 100000))
                path_to_tmp = os.path.join(os.path.dirname(__file__), file_name)
                if not os.path.exists(path_to_tmp):
                    break
            # save the script
            with open(path_to_tmp, "w") as tmp:
                tmp.write(complete)

            # make it executable
            sp.Popen("chmod +x \"{path}\"".format(path=path_to_tmp), shell=True).wait()

            # jobdispatch needs this with guillimin
            if dnsdomainname == "guillimin.clumeq.ca":
                os.environ["JOBDISPATCH_GPU_PARAM"] = "--gpu"

            ###################################################################
            # We make and run the jobdispatch shell line
            ###################################################################
            template = "jobdispatch --gpu --duree={walltime} \"{cmd}\""\
                .format(path=script_path,  walltime=walltime, cmd=path_to_tmp)

            sp.Popen(template, shell=True, stdin=sp.PIPE, stdout=sys.stdout).wait()

        print("benevolent_dictator - done")