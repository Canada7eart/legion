""" Extremely simple launch script. Should be improved. """
#!/usr/bin/env python2
from __future__ import print_function, with_statement, division, generators
import os, sys, re, threading, socket, time
import subprocess as sp
#Benevolant Dictator


PORT = 52341

def our_ip():
    return socket.gethostbyname(socket.gethostname())

def _acceptor_callback(conn, addr):
    print("_acceptor_callback: acceptor thread running.")

def _accept():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', PORT))
    s.listen(5)

    connected_client_qty = 0
    while True:
        print("_accept: Acceptor, online for ip %s:%d" % (our_ip(), PORT))
        conn, addr = s.accept()
        connected_client_qty += 1
        print("_accept: We just accepted a connection with %s" % str(addr))
        print("_accept: It is the node #%d" % connected_client_qty)

        args={
            "conn": conn,
            "addr": addr
        }

        new_thread = threading.Thread(target=lambda : _acceptor_callback(**args))
        new_thread.start()

def launch(script_path, project_name, walltime, number_of_nodes, number_of_gpus, job_name):
    launch_template = """#PBS -A %s
#PBS -l walltime=%d
#PBS -l nodes=%d:gpus=%d
#PBS -r n
#PBS -N %s

python '%s' --launcher-ip='%s' --launcher-port='%d' >> "/home/julesgm/task/exec.log"
""" % (
    project_name,
    walltime,
    number_of_nodes,
    number_of_gpus,
    job_name,
    script_path,
    our_ip(),
    PORT,
    )

    # from subprocess import Popen, PIPE, STDOUT
    # p = Popen(['grep', 'f'], stdout=PIPE, stdin=PIPE, stderr=STDOUT)    
    # grep_stdout = p.communicate(input=b'one\ntwo\nthree\nfour\nfive\nsix\n')[0]

    acceptor = threading.Thread(target=_accept)
    acceptor.start()
    print("launch: (still moving on)")
    process = sp.Popen("msub", shell=True, stdin=sp.PIPE, stdout=sp.PIPE,  stderr=sp.STDOUT)
    grep_stdout = process.communicate(input=launch_template)[0]    
    print("launch: " + str(grep_stdout))

    

