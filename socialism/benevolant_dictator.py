#!/usr/bin/env python2
from __future__ import print_function, with_statement, division, generators

""" Extremely simple launch script. Should be improved. """
import os, sys, re, threading, socket, time
import subprocess as sp
import param_serv.server

#Benevolant Dictator


PORT = 5234

def insert_tabs(text):
    return "\t" + text.replace("\n","\n\t")

def debugs(text):
    print(text)

def our_ip():
    return socket.gethostbyname(socket.gethostname())

def getTOD():
    return time.strftime("%H:%M:%S", time.gmtime())

def launch_server():
    db = {}
    db_rlock = threading.RLock()
    meta = {}
    meta_rlock = threading.RLock()

    acceptor = param_serv.server.AcceptorThread(meta, meta_rlock, db, db_rlock)
    acceptor.run()
    
    return acceptor
    
def launch_multiple(
    script_path, 
    project_name, 
    walltime, 
    number_of_nodes, 
    number_of_gpus, 
    job_name,
    task_name,  
    procs_per_job, 
    lower_bound, 
    upper_bound, 
    debug = False
    ):

    assert procs_per_job >= 1, "There needs to be at least one process per job."
    launch_template = \
"""
#PBS -A {project_name}
#PBS -l walltime={walltime}
#PBS -l nodes={number_of_nodes}:gpus={number_of_gpus}
#PBS -r n
#PBS -N {job_name}

#PBS -v MOAB_JOBARRAYINDEX

for i in $(seq 0 $(expr {procs_per_job} - 1))
do
    echo "starting job $i"
    python2 '{script_path}' --server_ip {server_ip} --task_name {task_name} --job_name {job_name} {debug} &
done
wait
""" \
.format(
    project_name=     project_name,
    walltime=         walltime,
    number_of_nodes=  number_of_nodes,
    number_of_gpus=   number_of_gpus,
    job_name=         job_name,
    task_name=        task_name,
    procs_per_job=    procs_per_job,
    script_path=      script_path,
    server_ip=        our_ip(),
    debug=            ("--debug" if debug else "")
)

    debugs("Running.")
    debugs("\nmsub will receive:")
    debugs(insert_tabs(launch_template) + "\n")  

    options = "-o '{here}/logs/out.log' -e '{here}/logs/err.log' -t {lower_bound}-{upper_bound}"\
        .format(
            here=os.path.dirname(__file__),
            lower_bound=lower_bound, 
            upper_bound=upper_bound,
            )

    if debug:
        env = {
            "PBS_NODENUM": "0",
            }
        env_code = "\n".join(["export {key}={value};".format(key=key, value=value) for key, value in env.items()]) + "\n"
        complete_code = env_code + "sh" + launch_template

        debugs("Env code:")
        debugs(insert_tabs(env_code))

        debugs("Complete code:")
        debugs(insert_tabs(complete_code))

        process = sp.Popen("sh --debug", shell=True, stdin=sp.PIPE, stdout=sys.stdout)
        stdout = process.communicate(complete_code)[0]    

    else:
        process = sp.Popen("msub {options}".format(options=options), shell=True, stdin=sp.PIPE, stdout=sys.stdout)
        stdout = process.communicate(launch_template)[0]    

    print("apres")
