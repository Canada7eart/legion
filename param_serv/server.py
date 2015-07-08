#!/usr/bin/env python2
from __future__ import print_function, with_statement, division, generators
import socket, json, struct
import threading
import sys, os, re, argparse, copy, time, datetime

from headers import *
from param_utils import *
import numpy as np

from traceback import print_exc

class AcceptorThread(threading.Thread):
    def __init__(self, meta, meta_rlock, db, db_rlock, server_port):
        super(self.__class__, self).__init__()
        self.meta = meta
        self.meta_rlock = meta_rlock
        self.db = db
        db["lol"] = Entry(np.ones([10, 10]))
        self.db_rlock = db_rlock
        self.server_port = server_port

    def run(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('', self.server_port))
        s.listen(1000)

        while True:
            conn, addr = s.accept()
            print('Connected by {addr}'.format(addr=addr))
            new_thread = ReceptionThread(conn, self.meta, self.meta_rlock, self.db, self.db_rlock)
            new_thread.start()


class ReceptionThread(threading.Thread):
    def __init__(self, conn, meta, meta_rlock, db, db_rlock):
        super(self.__class__, self).__init__()
        self.conn = conn
        self.db = db
        self.db_rlock = db_rlock
        self.meta = meta
        self.meta_rlock = meta_rlock
    
    def run(self):
        while True:
            header = self.conn.recv(struct.calcsize("i"))
            if header == HEADER_JSON:
                # Receive the json
                data = receive_json(self.conn)
                
                # To make checking less verbose
                if not "query_id" in data:
                    print("Server received a query without a query id. Killing connection and thread.")
                    break

                if data["query_id"] == query_HEADER_pull_full_param:                    
                    with self.db[data["param_name"]] as param_name:
                        target = copy.copy(param_name)
                    
                    answer = {
                        "query_id":    query_answer_HEADER_pull_full_param,
                        "query_name":  "answer_pull_full_param",
                        "param_name":  data["param_name"],
                        "param_shape": target.shape,
                        "param_dtype": repr(target.dtype)
                    }

                    send_json(self.conn, answer)
                    send_raw_numeric(self.conn, target)
                    continue

                elif data["query_id"] == query_HEADER_pull_part_param :
                    with self.db[data["param_name"]] as param_name:
                        target = copy.copy(param_name)

                    answer = {
                        "query_id":     query_answer_HEADER_pull_part_param,
                        "query_name":   "answer_pull_part_param",
                        "param_name":   data["param_name"],
                        "param_dtype":  repr(target.dtype),
                        "param_slice":  data["param_slice"],
                    }

                    send_json(self.conn, answer)
                    send_raw_numeric(self.conn, view_from_slice(target, data["param_slice"]))
                    continue

                elif data["query"] == "who_is_the_server":
                    with self.meta["server"] as server:
                        answer = {
                            "query": "answer_who_is_the_server",
                            "server": copy.copy(server)
                        }
                    send_json(self.conn, answer)
                else :
                    print("Exception: Unsupported query id #%d with name %s. closing the socket." % (data["query_id"], data.get(["query_name"], "[Query name not specified]")))
                    with self.meta["exceptions-log"] as exceptions_log:
                        exceptions_log.write("Exception: Unsupported query id. closing the socket.")
                    break

            else:
                print("UNHANDLED HEADER %d" % (header))

        self.conn.close()    