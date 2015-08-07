#!/usr/bin/env python2
from __future__ import print_function, with_statement, division, generators, absolute_import

import socket, os, sys, argparse
from socialism.param_serv.param_utils import *
from socialism import benevolant_dictator

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', default=False, action="store_true")
    args = parser.parse_args()

    debug = args.debug
    debug_pycharm = True
    soc = benevolant_dictator.Server()
    server = soc.launch_server()
    filename = 'exemple_user_script.py'
    base_path = os.path.dirname(os.path.dirname(__file__))

    if debug:
        soc.launch_clients(
            user_script_path= os.path.join(base_path, filename),
            walltime=         10,
            job_name=         "0",
            task_name=        "debug",
            procs_per_job=1,
            debug=            True,
            theano_flags="device=cpu,floatX=float32",
            debug_pycharm=    debug_pycharm,
            user_script_args= "",
            )

    else:
        soc.launch_clients(
            user_script_path= os.path.join("/home/julesgm/task/", filename),
            walltime=         10,
            number_of_nodes=  1,
            job_name=         "0",
            task_name=        "debug",
            procs_per_job=    1,
            allocation_name=  "jvb-000-aa",
            user_script_args= "--experiment_dir=/home/julesgm/NIPS/experiments/experiment_dir_1 --output_server_params_desc_path=server_params_desc.json",
            theano_flags=     "device=gpu0,floatX=float32",
            )

    print("launcher - done")