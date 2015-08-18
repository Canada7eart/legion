#! /software6/apps/python/2.7.5/bin/python 
from __future__ import print_function, division, absolute_import
__author__ = 'Jules Gagnon-Marchand'
import os, sys, re, argparse

print("importing legion")
from legion as Server()
from legion.param_serv.param_utils import *

def profile():
    import yappi

    print("starting.")
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', default=False, action="store_true")
    args = parser.parse_args()

    debug = False
    debug_pycharm = True

    soc = Server()
    path = os.path.join(os.path.dirname(__file__), 'tuto0.py')

    try:
        yappi.start()
	
        if debug:
            soc.launch_clients(user_script_path=  path,
                               job_name=          "0",
                               debug=             True,
                               debug_pycharm=     True,
                               )

        else:
            print("starting.")
            soc.launch_clients(user_script_path=  path,
                               job_name=          "soc_blocks_tuto0",
                               instances=         5,
                               walltime=          "6:00:00",
                               allocation_name=   "jvb-000-ag",
                               )
    	
        soc.join_threads()
   
    finally:
	print("printing profiling information")
        yappi.get_func_stats().print_all()
        yappi.get_thread_stats().print_all()

    print("launcher - done")



def main():
    print("starting.")
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', default=False, action="store_true")
    args = parser.parse_args()

    debug = False
    debug_pycharm = True

    soc = benevolant_dictator.Server()

    path = os.path.join(os.path.dirname(__file__), 'tuto0.py')

    if debug:
        soc.launch_clients(user_script_path=  path,
                           job_name=          "0",
                           debug=             True,
                           debug_pycharm=     True,
                           )

    else:
        soc.launch_clients(user_script_path=  path,
                           job_name=          "soc_blocks_tuto0",
                           instances=         5,
                           walltime=          "6:00:00",
                           allocation_name=   "jvb-000-ag",
                           )
    
    print("launcher - done")

if __name__ == "__main__":
    profile()

