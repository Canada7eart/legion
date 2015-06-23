""" Extremely simple launch script. Should be improved. """
#!/usr/bin/env python2
from __future__ import print_function, with_statement, division, generators
import os, sys, re, threading, socket, time
import subprocess as sp

#Benevolant Dictator


PORT = 5234

def our_ip():
    return socket.gethostbyname(socket.gethostname())

def getTOD():
    return time.strftime("%H:%M:%S", time.gmtime())

def launch_multiple(script_path, project_name, walltime, number_of_nodes, number_of_gpus, job_name, procs_per_job, lower_bound, upper_bound):
    assert procs_per_job >= 1, "There needs to be at least one process per job."

    launch_template = \
"""
#PBS -A {project_name}
#PBS -l walltime={walltime}
#PBS -l nodes={number_of_nodes}:gpus={number_of_gpus}
#PBS -r n
#PBS -N {job_name}

#PBS -v MOAB_JOBARRAYINDEX

module load compilers/intel/12.0.4

for i in $(seq 0 $(expr {number_of_procs} - 1))
do
    echo "starting job $i"
    python '{script_path}' --path {log_path} > ./launched_python_script_log_$i.log &
done
wait
""" \
.format(
**{   
    "project_name":     project_name,
    "walltime':         walltime",
    "number_of_nodes":  number_of_nodes,
    "number_of_gpus":   number_of_gpus,
    "job_name':         job_name",
    "number_of_procs":  number_of_procs,
    "script_path":      script_path,
    "log_path":         "/home/julesgm/task/files/inner.log",
})

    print("Running.")
    print("Still opened.")
    print(launch_template)

    regular = "msub -o '/home/julesgm/task/out.log' -e '/home/julesgm/task/err.log' -t %d-%d" % (lower_bound, upper_bound)
    process = sp.Popen(regular, shell=True, stdin=sp.PIPE)
    grep_stdout = process.communicate(input=launch_template)[0]    
    print("apres")
