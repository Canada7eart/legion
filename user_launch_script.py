#!/usr/bin/env python2
from __future__ import print_function, with_statement, division, generators
from socialism import benevolant_dictator
import socket, os, sys

if __name__ == "__main__": 

    debug = True

    server_thread = benevolant_dictator.launch_server() 

    path = os.path.join(os.path.dirname(__file__), 'user_compute_script.py') 

    if debug:
        benevolant_dictator.launch_multiple(
            script_path=path, 
            project_name="jvb-000-aa", 
            walltime=10, 
            number_of_nodes=4, 
            number_of_gpus=2, 
            job_name="0",
            task_name="debug",
    	    procs_per_job=1,
            lower_bound=0,
            upper_bound=0,
            debug = True,
            )

    else:
        benevolant_dictator.launch_multiple(
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
            )

    server_thread.join()
