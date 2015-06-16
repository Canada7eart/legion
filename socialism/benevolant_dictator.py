""" Extremely simple launch script. Should be improved. """
#!/usr/bin/env python2
from __future__ import print_function, with_statement, division, generators
import os, sys, re, threading, socket, time
import subprocess as sp
#Benevolant Dictator


PORT = 52341

def our_ip():
    return socket.gethostbyname(socket.gethostname())


def launch(script_path, project_name, walltime, number_of_nodes, number_of_gpus, job_name):
    launch_template = """#PBS -A %s
#PBS -l walltime=%d
#PBS -l nodes=%d:gpus=%d
#PBS -r n
#PBS -N %s

python '%s' --path %s >> "/home/julesgm/task/exec.log"
""" % (
    project_name,
    walltime,
    number_of_nodes,
    number_of_gpus,
    job_name,
    script_path,
    "/home/julesgm/task/files/",
    )

    # from subprocess import Popen, PIPE, STDOUT
    # p = Popen(['grep', 'f'], stdout=PIPE, stdin=PIPE, stderr=STDOUT)    
    # grep_stdout = p.communicate(input=b'one\ntwo\nthree\nfour\nfive\nsix\n')[0]

    process = sp.Popen("msub", shell=True, stdin=sp.PIPE, stdout=sp.PIPE,  stderr=sp.STDOUT)
    grep_stdout = process.communicate(input=launch_template)[0]    
    print("launch: " + str(grep_stdout))

    

