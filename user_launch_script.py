#!/usr/bin/env python2
from __future__ import print_function, with_statement, division, generators
from socialism import benevolant_dictator
import socket, os, sys

if __name__ == "__main__": 
    debug = True
    path = "{here}/user_compute_script.py".format(here=os.path.dirname(__file__))

    print(path)


    if debug:
        benevolant_dictator.launch_multiple(
            script_path=path, 
            project_name="jvb-000-aa", 
            walltime=10, 
            number_of_nodes=4, 
            number_of_gpus=2, 
            job_name="0",
    	    procs_per_job=1,
            lower_bound=0,
            upper_bound=0,
            debug = True,
            )

    else:
        benevolant_dictator.launch_multiple(
            script_path="{here}/user_compute_script.py".format(here=os.path.dirname(__file__)), 
            project_name="jvb-000-aa", 
            walltime=10, 
            number_of_nodes=4, 
            number_of_gpus=2, 
            job_name="0",
            procs_per_job=8,
            lower_bound=0,
            upper_bound=0,
            )
