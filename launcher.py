#!/usr/bin/env python2
from __future__ import print_function, with_statement, division, generators
""" THIS IS AN EXAMPLE : this is the type of launch script that it is suggested that you use """


from socialism import benevolant_dictator
import socket, os, sys, argparse
from socialism.param_serv.param_utils import *

if __name__ == "__main__":

    debug = False
    debug_pycharm = True
    soc = benevolant_dictator.Server()
    server = soc._launch_server()

    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        path = os.path.join(os.path.dirname(__file__), 'user_script.py')

    if debug:
        soc._launch_multiple(
            user_script_path=path,
            project_name="jvb-000-aa",
            walltime=10,
            number_of_nodes=1,
            number_of_gpus=2,
            job_name="0",
            task_name="debug",
            procs_per_job=1,
            lower_bound=0,
            upper_bound=0,
            debug=True,
            debug_pycharm=debug_pycharm
            )

    else:
        soc._launch_multiple(
            user_script_path=path,
            project_name="jvb-000-aa",
            walltime=10,
            number_of_nodes=1,
            number_of_gpus=2,
            job_name="0",
            task_name="debug",
            procs_per_job=8,
            lower_bound=0,
            upper_bound=0,
            user_script_args="--experiment_dir=/home/julesgm/NIPS/experiments/experiment_dir_1 --output_server_params_desc_path=server_params_desc.json",
            theano_flags="device=gpu0,floatX=float32",
            )


    print("launcher - done")