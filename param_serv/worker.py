#!/usr/bin/env python2
from __future__ import print_function, with_statement, division, generators
# Echo server program
import socket, json, struct
import threading
from threading import Queue
import sys, os, re, argparse, copy, time, datetime


HEADER_JSON = 1
HEADER_NUMERIC = 2

query_HEADER_pull_full_param = 3
query_HEADER_pull_part_param = 4

query_answer_HEADER_pull_full_param = 5

def now_milliseconds():
    now = datetime.datetime.now()
    return (now.days * 24 * 60 * 60 + now.seconds) * 1000 + now.microseconds / 1000.0


def send_json(conn, dict_to_transform):
    data = son.dumps(dict_to_transform)
    conn.send(HEADER_JSON)
    conn.send(len(data))
    conn.send(data)


def view_from_slice(tensor, _slice):
    """ I'm 100%% sure there is a better way to do this. """
    formatted_slice = []
    for i in xrange(len(slice.shape)):
        formatted_slice.append([j for j in xrange(_slice[i, j])])
    return tensor.__getitem__(formatted_slice)


def send_raw_numeric(conn, numeric):
    flat = numeric.flatten()
    data = struct.pack(flat)
    conn.send(HEADER_NUMERIC)
    conn.send(len(data))
    conn.send(data)


def we_are_not_the_server(meta, meta_rlock, orig):
    with meta_rlock:
        server_ip = copy.copy(self.meta["server"])
    
    return {
        "query":"special_error",
        "type":"we_are_the_server",
        "server":server_ip,
        "in_resp":orig
        }


def server_compatibility_check(meta, meta_rlock, query):
    with meta_rlock:
        test = query in meta["server-queries"]

    return test    

def receive_json(conn):
    bytes_to_receive = conn.recv(struct.calcsize("i"))
    raw = conn.recv(bytes_to_receive)
    data = json.loads(raw)
    print(data)
    return data


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
                    with db_rlock:
                        target = copy.copy(self.db[data["param_name"]])
                    
                    answer = {
                        "query_id":     query_answer_HEADER_pull_full_param,
                        "query_name":   "answer_pull_full_param",
                        "param_name":   data["param_name"],
                        "param_shape":  target.shape,
                        "param_dtype":  repr(target.dtype)
                    }

                    send_json(conn, answer)
                    send_raw_numeric(conn, target)
                    continue

                elif data["query_id"] == query_HEADER_pull_part_param :
                    with db_rlock:
                        target = copy.copy(self.db[data["param_name"]]

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
                    with meta_rlock:
                        answer = {
                            "query": "answer_who_is_the_server",
                            "server": copy.copy(self.meta["server"])
                        }
                    send_json(self.conn, answer)

                elif data["query_id"] == None :
                    print("Exception: Received a query without a query_id. Closing the socket.")

                    break;
                else :
                    print("Exception: Unsupported query id #%d with name %s. closing the socket." % (data["query_id"], data.get(["query_name"], "[Query name not specified]")))
                    with meta_rlock:
                        meta["exceptions-log"].write("Exception: Unsupported query id. closing the socket.")
                    break;
            else:
                print("UNHANDLED HEADER %d" % (header))

        conn.close()    

EmissionThread_state_INIT = 1


class EmissionThread(threading.Thread):
    def __init__(self, conn, meta, meta_rlock, db, db_rlock):
        self.conn = conn
        self.meta = meta
        self.meta_rlock = meta_rlock
        self.db = db
        self.db_rlock = db_rlock
        
    def start(self):



class AcceptorThread(threading.Thread):
    def __init__(self, meta, meta_rlock, db, db_rlock):
        self.meta = meta
        self.meta_rlock = meta_rlock
        self.db = db
        self.db_rlock = db_rlock

    def start(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('', PORT))
        s.listen(200)

        while True:
            conn, addr = s.accept()
            print 'Connected by', addr
            new_thread = ReceptionThreadThread(conn, meta, meta_rlock, db, db_rlock)
            new_thread.run()


class ConnectorThread(threading.Thread):
    def __init__(self, meta, meta_rlock, db, db_rlock, ip, port):
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
        "exceptions-log":open("./exceptions.log", "a"),
    }
    meta_rlock = threading.RLock()

    acceptor_thread = AcceptorThread(meta, meta_rlock, db, db_rlock)
    acceptor_thread.run()

    connector_thread = ConnectorThread(meta, meta_rlock, db, db_rlock, IP, PORT)
    connector_thread.run()

    acceptor_thread.join()
    connector_thread.join()
    