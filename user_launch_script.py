#!/usr/bin/env python2
from __future__ import print_function, with_statement, division, generators
import socialism.benevolant_dictator as bd
import socket

if __name__ == "__main__": 
    bd.launch(
        script_path="/home/julesgm/task/user_compute_script.py", 
        project_name="jvb-000-aa", 
        walltime=10, 
        number_of_nodes=4, 
        number_of_gpus=2, 
        job_name="experims"
        )

