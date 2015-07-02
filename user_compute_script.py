#!/usr/bin/env python2
from __future__ import print_function, with_statement, division, generators
""" Extremely simple launch script. Should be improved. """


PORT = 6000
import os, sys, re, threading, socket, argparse, time, threading
import subprocess as sp
import pg8000
import database_interface as dbi
import param_serv.worker

def getTOD():
    return time.strftime("%H:%M:%S", time.gmtime())

def header():
    return "PBS_NODENUM#%s - %s" % (getTOD(), os.environ["PBS_NODENUM"], )

# print_with_header
def pwh(text):
    print("{header}: {text}".format(
        header=header(), 
        text=text))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sql_server_ip',   nargs=1, type=str)
    parser.add_argument('--sql_server_port', nargs=1, type=str)
    parser.add_argument('--job_name',        nargs=1, type=str)
    parser.add_argument('--debug',           action="store_true")

    args = parser.parse_args()

    pwh("Saving ip to database.")
    
    continue_looping = True

    while continue_looping:

        try:
            db = dbi.Db(pg8000, args.job_name[0]) 
            server_ip, server_port = db.get_server_ip_and_port()
            continue_looping = False

        except Exception, err:
            print err
            time.sleep(0.5)

    db.save_proc_entry(PORT)

    # CONNECT TO THE SERVER 
    param_db = {}
    param_db_rlock = threading.RLock()
    meta = {
        "server_queries":{
            "pull_part_param",
            "pull_full_param",   
        },
        "exceptions-log":open("./exceptions.log", "a"),
    }
    meta_rlock = threading.RLock()

    worker.connector_thread = ConnectorThread(meta, meta_rlock, param_db, param_db_rlock)
    worker.connector_thread.run()

    # DIE
    db.update_proc_state(os.getpid(), "DEAD")
    pwh("Done.")

if __name__ == '__main__':
    main()
