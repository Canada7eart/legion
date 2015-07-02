#!/usr/bin/env python2
from __future__ import print_function, with_statement, division, generators
import socket, json, struct
import threading
import sys, os, re, argparse, copy, time, datetime

from traceback import print_exc

from headers import *
from param_utils import *

class ConnectorThread(threading.Thread):
    def __init__(self, meta, meta_rlock, db, db_rlock, ip, port):
        super(self.__class__, self).__init__()
        
        self.meta = meta
        self.meta_rlock = meta_rlock
        self.db = db
        self.db_rlock = db_rlock
        self.ip = ip
        self.port = port

    def start(self):
        with meta_rlock:
            ips_we_want = copy.copy(meta["nodes"])

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn = s.create_connection((self.ip, self.port), timeout=20)
            
        if conn:
            state = EmissionThread_state_INIT
             
            #while True:
            for i in range(10):
                if state == EmissionThread_state_INIT:
                    print("would be emitting stuff")
                    time.sleep(0.01)

        else:
            print("WE FAILED") 


if __name__ == '__main__':

    db = {}
    db_rlock = threading.RLock()
    meta = {
        "server_queries":{
            "pull_part_param",
            "pull_full_param",   
        },
        "exceptions-log": open("./exceptions.log", "a"),
    }

    meta_rlock = threading.RLock()

    acceptor_thread = AcceptorThread(meta, meta_rlock, db, db_rlock)
    acceptor_thread.run()

    connector_thread = ConnectorThread(meta, meta_rlock, db, db_rlock, IP, PORT)
    connector_thread.run()

    acceptor_thread.join()
    connector_thread.join()
    