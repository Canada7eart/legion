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
            header = struct.unpack("i", self.conn.recv(struct.calcsize("i")))[0]
            if header == HEADER_JSON:
                # Receive the json
                data = receive_json(self.conn)
                

                # To make checking less verbose
                if not "query_id" in data:
                    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                    print(">>>> server - Server received a query without a query id. Killing connection and thread.")
                    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                    break

                # explicitely cash query_id (hashmap lookups are still expensive; we have an interpreter, not a static, aot or jit compiler)
                query_id = data["query_id"]

                if query_id == query_HEADER_pull_full_param:
                    param_name = data["param_name"]

                    with self.db[param_name] as param:
                        numeric_data = param.astype(np.int64).tostring()
                        target_shape_str = str(param.shape)
                        target_dtype_str = str(param.dtype)
                    
                    answer = {
                        "query_id":    query_answer_HEADER_pull_full_param,
                        "query_name":  "answer_pull_full_param",
                        "param_name":  param_name,
                        "param_shape": target_shape_str,
                        "param_dtype": target_dtype_str
                    }

                    send_json(self.conn, answer)
                    
                    self.conn.sendall(
                        struct.pack(
                            "ii%ds" % len(numeric_data), 
                            HEADER_NUMERIC, 
                            len(numeric_data), 
                            numeric_data
                            )
                        )
                    
                    continue

                elif query_id == query_HEADER_pull_part_param :
                    param_name = data["param_name"]
                    param_slice = data["param_slice"]

                    with self.db[param_name] as param:
                        numeric_data = view_from_slice(param, param_slice).tostring()
                        target_shape_str = str(param.shape)
                        target_dtype_str = str(param.dtype)


                    answer = {
                        "query_id":     query_answer_HEADER_pull_part_param,
                        "query_name":   "answer_pull_part_param",
                        "param_name":   param_name,
                        "param_dtype":  target_dtype_str,
                        "param_slice":  param_slice,
                    }

                    send_json(self.conn, answer)
                    send_raw_numeric(self.conn, )

                    continue

                elif query_id == "who_is_the_server":
                    with self.meta["server"] as server:
                        answer = {
                            "query": "answer_who_is_the_server",
                            "server": copy.copy(server)
                        }
                    send_json(self.conn, answer)
                else :
                    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                    print(">>>> server - Exception: Unsupported query id #%d with name %s. closing the socket." % (data["query_id"], data.get(["query_name"], "[Query name not specified]")))
                    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                    with self.meta["exceptions-log"] as exceptions_log:
                        exceptions_log.write("Exception: Unsupported query id. closing the socket.")
                    break

            else:
                print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                print(">>>>> server - UNHANDLED HEADER '{header}'".format(header=header))
                print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")

        self.conn.close()    