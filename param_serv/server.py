#!/usr/bin/env python2
from __future__ import print_function, with_statement, division, generators
import socket, json, struct
import threading
import sys, os, re, argparse, copy, time, datetime

from headers import *
from param_utils import *
from traceback import print_exc

class AcceptorThread(threading.Thread):
    def __init__(self, meta, meta_rlock, db, db_rlock):
        self.meta = meta
        self.meta_rlock = meta_rlock
        self.db = db
        self.db_rlock = db_rlock

    def start(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('', PORT))
        s.listen()

        while True:
            conn, addr = s.accept()
            print('Connected by {addr}'.format(addr=addr))
            new_thread = ReceptionThreadThread(conn, meta, meta_rlock, db, db_rlock)
            new_thread.run()


class ReceptionThread(threading.Thread):
    def __init__(self, conn, meta, meta_rlock, db, db_rlock):
        self.conn = conn
        self.db = db
        self.db_rlock = db_rlock
        self.meta = meta
        self.meta_rlock = meta_rlock
    
    def start(self):
        while True:
            header = conn.recv(struct.calcsize("i"))
            if header == HEADER_JSON:
                # Receive the json
                data = receive_json(conn)
                
                # To make checking less verbose
                data["query_id"] = data.get("query_id", None)

                # Check if it's a server query and we are the server
                if (data["for_server"] or server_compatibility_check(data["query"])) and not self.we_are_the_server:
                    # we only lock when the function doesn't take the lock in argument
                    send_json(we_are_not_the_server(meta, meta_rlock, data))
                    continue

                if data["query_id"] == query_HEADER_pull_full_param and data.get("for_server", False):                    
                    with self.db[data["param_name"]] as param_name:
                        target = copy.copy(param_name)
                    
                    answer = {
                        "query_id":    query_answer_HEADER_pull_full_param,
                        "query_name":  "answer_pull_full_param",
                        "param_name":  data["param_name"],
                        "param_shape": target.shape,
                        "param_dtype": repr(target.dtype)
                    }

                    send_json(conn, answer)
                    send_raw_numeric(conn, target)
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

                    send_json(conn, answer)
                    send_raw_numeric(conn, view_from_slice(target, data["param_slice"]))
                    continue

                elif data["query"] == "who_is_the_server":
                    with self.meta["server"] as server:
                        answer = {
                            "query": "answer_who_is_the_server",
                            "server": copy.copy(server)
                        }
                    send_json(self.conn, answer)

                elif data["query_id"] == None :
                    print("Exception: Received a query without a query_id. Closing the socket.")

                    break;

                else :
                    print("Exception: Unsupported query id #%d with name %s. closing the socket." % (data["query_id"], data.get(["query_name"], "[Query name not specified]")))
                    with meta["exceptions-log"] as exceptions_log:
                        exceptions_log.write("Exception: Unsupported query id. closing the socket.")
                    break;

            else:
                print("UNHANDLED HEADER %d" % (header))

        conn.close()    