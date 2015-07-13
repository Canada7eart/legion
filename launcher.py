#!/usr/bin/env python2
from __future__ import print_function, with_statement, division, generators
from socialism import benevolant_dictator
import socket, os, sys
from param_serv.param_utils import *

if __name__ == "__main__":
    server_port = 2001
    debug = True
    debug_pycharm = True
    soc = benevolant_dictator.Socialism(our_ip(), server_port)
    server = soc._launch_server(server_port)

    path = os.path.join(os.path.dirname(__file__), 'client_backend.py')

    if debug:
        soc._launch_multiple(
            script_path=path,
            project_name="jvb-000-aa",
            walltime=10,
            number_of_nodes=1,
            number_of_gpus=2,
            job_name="0",
            task_name="debug",
            procs_per_job=1,
            lower_bound=0,
            upper_bound=0,
            server_port=server_port,
            debug=True,
            debug_pycharm=debug_pycharm
            )

    else:
        soc._launch_multiple(
            script_path=path,
            project_name="jvb-000-aa",
            walltime=10,
            number_of_nodes=4,
            number_of_gpus=2,
            job_name="0",
            task_name="debug",
            procs_per_job=8,
            lower_bound=0,
            upper_bound=0,
            server_port=server_port,
            )


