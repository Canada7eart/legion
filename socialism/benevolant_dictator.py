""" Extremely simple launch script. Should be improved. """
#!/usr/bin/env python2
from __future__ import print_function, with_statement, division, generators
import os, sys, re, threading, socket, time
import subprocess as sp
#Benevolant Dictator


PORT = 52341

def our_ip():
    return socket.gethostbyname(socket.gethostname())

def getTOD():
    return time.strftime("%H:%M:%S", time.gmtime())

def launch(script_path, project_name, walltime, number_of_nodes, number_of_gpus, job_name, number_of_procs):
    launch_template = """#PBS -A %s
#PBS -l walltime=%d
#PBS -l nodes=%d:gpus=%d
#PBS -r n
#PBS -N %s

#PBS -v MOAB_JOBARRAYINDEX

module load compilers/intel/12.0.4

UPPER_LIMIT=`expr ${PBS_JOBARRAYINDEX} + %d`

for i in $(seq ${PBS_JOBARRAYINDEX} ${UPPER_LIMIT})
do
    echo "starting job $i"
    python '%s' --path %s > ./launched_python_script_log_$i.log &
done
wait
""" % (
    project_name,
    walltime,
    number_of_nodes,
    number_of_gpus,
    job_name,
    number_of_procs,
    script_path,
    "/home/julesgm/task/files/lol.log",
    #"/Users/jules/Documents/LISA/task/files/lol.log", 
    )

    # from subprocess import Popen, PIPE, STDOUT
    # p = Popen(['grep', 'f'], stdout=PIPE, stdin=PIPE, stderr=STDOUT)    
    # grep_stdout = p.communicate(input=b'one\ntwo\nthree\nfour\nfive\nsix\n')[0]
    print("Running.")
    print("Still opened.")
    print(launch_template)
    test = "sh"
    regular = "msub -o '/home/julesgm/task/out.log' -e '/home/julesgm/task/err.log' -t 0-100"
    process = sp.Popen(regular, shell=True, stdin=sp.PIPE)
    grep_stdout = process.communicate(input=launch_template)[0]    
    print("apres")
