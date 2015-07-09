#!/usr/bin/env python2
from __future__ import print_function, with_statement, division, generators
import argparse
""" Extremely simple launch script. Should be improved. """


PORT = 6000
#import database_interface as dbi

import param_serv.worker
from param_serv.param_utils import *


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sql_server_ip',   nargs=1, type=str)
    parser.add_argument('--sql_server_port', nargs=1, type=str)
    parser.add_argument('--job_name',        nargs=1, type=str)
    parser.add_argument('--task_name',       nargs=1, type=str)
    parser.add_argument('--server_ip',       nargs=1, type=str)
    parser.add_argument('--server_port',     nargs=1, type=int)
    parser.add_argument('--debug',           action="store_true")

    args = parser.parse_args()

    #pwh("Saving ip to database.")
    
    continue_looping = True

    """
    while continue_looping:

        try:
            # db = dbi.Db(pg8000, args.task_name[0], args.job_name[0]) 
            # server_ip, server_port = db.get_server_ip_and_port()
            continue_looping = False

        except Exception, err:
            print_exc()
            time.sleep(0.5)

    db.save_proc_entry(PORT)
    """

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

    worker_connector_thread = param_serv.worker.ConnectorThread(meta, meta_rlock, param_db, param_db_rlock, args.server_ip[0], args.server_port[0])
    worker_connector_thread.start()

    # DIE
    # param_db.update_proc_state(os.getpid(), "DEAD")
    pwh("Done.")

if __name__ == '__main__':
    main()
