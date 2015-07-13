#!/usr/bin/env python2
from __future__ import print_function, with_statement, division, generators

""" Extremely simple launch script. Should be improved. """
import os, sys, re, threading, socket, time
import subprocess as sp
import param_serv.server

from param_serv.param_utils import *

class Client(object):
    def __init__(self):
        # we minimise the number of hash map lookups by saving refs to values used more than once
        server_ip = os.environ["SOCIALISM_server_ip"]
        server_port = os.environ["SOCIALISM_server_port"]

        debug = os.environ.get("SOCIALISM_debug", False)
        pycharm_debug = os.environ.get("SOCIALISM_pycharm_debug", False)

        meta = {
            "job_name": os.environ["SOCIALISM_job_name"],
            "task_name": os.environ["SOCIALISM_task_name"],
            "server_ip": server_ip,
            "server_port": server_port
        }

        param_db = {}
        self.worker_connector_thread = param_serv.worker.ConnectorThread(meta, param_db, server_ip, server_port)
        self.worker_connector_thread.start()


class Server(object):
    def __init__(self, server, port):
        pass

    def _launch_server(server, port):
        db = {}
        db_rlock = threading.RLock()
        meta = {}
        meta_rlock = threading.RLock()

        acceptor = param_serv.server.AcceptorThread(
            meta=meta,
            meta_rlock=meta_rlock,
            db=db,
            db_rlock=db_rlock,
            server_port=port
            )

        acceptor.start()

        return acceptor

    def _launch_multiple(self,
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
        server_port,
        debug = False,
        debug_pycharm = False
        ):

########################################################
# grunt work
########################################################
        pydev=""
        executable="python2"

        ############
        # function argument/param consistency check; this is a directly user exposed function.
        # TODO: this, tightly, when we have consistent basic functionality
        ############
        assert procs_per_job >= 1, "There needs to be at least one process per job."

        ############
        # Create the shell script that is going to be used to launch the jobs.
        # TODO: add jobdispatch integration
        ############

        # putting raw text like this in a source file is really ugly, but is easier for development, right now.
        # will be modified to add jobdispatch, and then, might be moved to an external file.
        launch_template = \
"""
#PBS -A {project_name}
#PBS -l walltime={walltime}
#PBS -l nodes={number_of_nodes}:gpus={number_of_gpus}
#PBS -r n
#PBS -N {job_name}

#PBS -v MOAB_JOBARRAYINDEX

export PYTHONPATH="$PYTHONPATH":"{pydev}"

for i in $(seq 0 $(expr {procs_per_job} - 1))
do
    echo "starting job $i"
    {executable} '{script_path}' --pycharm_debug --server_ip \'{server_ip}\' --server_port \'{server_port}\' --task_name \'{task_name}\' --job_name \'{job_name}\' {debug} &
done
wait
""" \
            .format(
                pydev=            pydev,
                executable=       executable,
                project_name=     project_name,
                walltime=         walltime,
                number_of_nodes=  number_of_nodes,
                number_of_gpus=   number_of_gpus,
                job_name=         job_name,
                task_name=        task_name,
                procs_per_job=    procs_per_job,
                script_path=      script_path,
                server_ip=        our_ip(),
                server_port=      server_port,
                debug=            ("--debug" if debug else ""),
            )

        options = "-o '{here}/logs/out.log' -e '{here}/logs/err.log' -t {lower_bound}-{upper_bound}" \
            .format(
                here=           os.path.dirname(__file__),
                lower_bound=    lower_bound,
                upper_bound=    upper_bound,
            )

########################################################
# pycharm remote debugging
########################################################
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

        else:
            process = sp.Popen("msub {options}".format(options=options), shell=True, stdin=sp.PIPE, stdout=sys.stdout)
            stdout = process.communicate(launch_template)[0]

