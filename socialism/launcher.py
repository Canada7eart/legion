#!/usr/bin/env python2
from __future__ import print_function, with_statement, division, generators

from socialism import benevolant_dictator
import socket, os, sys, argparse
from param_serv.param_utils import *

if __name__ == "__main__":

    debug = False
    debug_pycharm = True
    soc = benevolant_dictator.Server()
    server = soc.launch_server()


    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'exemple_user_script.py')


    if debug:
        soc.launch_clients(
            user_script_path=path,
            project_name="jvb-000-aa",
            walltime=10,
            number_of_nodes=1,
            number_of_gpus=2,
            job_name="0",
            task_name="debug",
            procs_per_job=1,
            debug=True,
            debug_pycharm=debug_pycharm
            )

    else:
        soc.launch_clients(
            user_script_path=path,
            project_name="jvb-000-aa",
            walltime=10,
            number_of_nodes=1,
            number_of_gpus=2,
            job_name="0",
            task_name="debug",
            procs_per_job=8,
            user_script_args="--experiment_dir=/home/julesgm/NIPS/experiments/experiment_dir_1 --output_server_params_desc_path=server_params_desc.json",
            theano_flags="device=gpu0,floatX=float32",
            )


    print("launcher - done")