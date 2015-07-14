#!/usr/bin/env python2
from __future__ import print_function, with_statement, division, generators
import copy
from traceback import format_exc

import numpy as np

from param_utils import *


class AcceptorThread(threading.Thread):
    def __init__(self, meta, meta_rlock, db, db_rlock, server_port):
        super(self.__class__, self).__init__()
        self.meta = meta
        self.meta_rlock = meta_rlock
        self.db = db
        db["test"] = Entry(np.ones([10, 10]))
        self.db_rlock = db_rlock
        self.server_port = server_port
        self.sock = None

    def run(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.bind(('', self.server_port))
            self.sock.listen(100)

        except socket.error, serr:
            if serr.errno == 48:
                pwh(format_exc())
                exit(-1)

        try:
            while True:
                print("waiting for a connection")
                conn, addr = self.sock.accept()
                print("established new connection")
                new_thread = ReceptionThread(conn, self.meta, self.meta_rlock, self.db, self.db_rlock)
                new_thread.start()

        finally:
            if self.sock is not None:
                self.sock.close()

class ReceptionThread(threading.Thread):
    def __init__(self, conn, meta, meta_rlock, db, db_rlock):
        super(self.__class__, self).__init__()
        self.conn = conn
        self.db = db
        self.db_rlock = db_rlock
        self.meta = meta
        self.meta_rlock = meta_rlock
    
    def run(self):
        try:
            while True:
                try:
                    print("waiting for a query")
                    data = receive_json(self.conn)
                    print("received a query")
                except socket.error, serr:
                    if serr.errno == 104:
                        pwh(">>>> server - The client closed the connection.")
                    else :
                        pwh(">>>> server - recv failed; unknown error of no {errno}".format(errno=serr.errno))
                        raise serr
                    return

                # To make checking less verbose
                if not "query_id" in data:
                    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                    print(">>>> server - Server received a query without a query id. Killing connection and thread.")
                    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                    break

                # explicitly cash query_id (hash map lookups are still expensive;
                # we have an interpreter, not a static, aot or jit compiler)
                query_id = data["query_id"]

                if query_id == query_HEADER_pull_full:
                    param_name = data["name"]

                    with self.db[param_name] as param:
                        numeric_data = param.tobytes()
                        target_shape_str = copy.copy(param.shape)
                        target_dtype_str = str(param.dtype)

                    answer = {
                        "query_id":    query_answer_HEADER_pull_full,
                        "query_name":  "answer_pull_full",
                        "name":  param_name,
                        "shape": target_shape_str,
                        "dtype": target_dtype_str
                    }

                    send_json(self.conn, answer)
                    print(">>>>> server - numeric_data size: %i" % len(numeric_data))
                    send_numeric_from_bytes(self.conn, numeric_data)

                    continue

                elif query_id == query_HEADER_pull_part:
                    param_name = data["name"]
                    param_slice = data["slice"]

                    with self.db[param_name] as param:
                        numeric_data = view_from_slice(param, param_slice).tostring()
                        target_shape_str = str(param.shape)
                        target_dtype_str = str(param.dtype)

                    answer = {
                        "query_id":    query_answer_HEADER_pull_part,
                        "query_name":  "answer_pull_part",
                        "name":        param_name,
                        "dtype":       target_dtype_str,
                        "slice":       param_slice,
                    }

                    send_json(self.conn, answer)
                    assert False, "TODO"
                    # send_raw_numeric(self.conn, )

                    continue
                elif query_id == query_HEADER_push_full:
                    param_name = data["name"]
                    numeric_data = receive_numeric(self.conn)

                    with self.db[param_name] as _:
                        numeric_data = numeric_data.reshape(data.get("shape", self.db[param_name].inner.shape))
                        numeric_data = numeric_data.astype(data.get("dtype", self.db[param_name].inner.dtype))
                        self.db[param_name].inner = data["alpha"] * self.db[param_name].inner + \
                            data["beta"] * numeric_data

                    continue
                elif query_id == query_HEADER_push_part:
                    print("server push_part -> not yet supported")
                    continue
                else:
                    pwh(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                    pwh(">>>> server - Exception: Unsupported query id #%d with name %s. closing the socket." % (data["query_id"], data.get("[query_name]", "[Query name not specified]")))
                    pwh(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")

                    with self.meta["exceptions-log"] as exceptions_log:
                        exceptions_log.write("Exception: Unsupported query id. closing the socket.")

                    break

        finally:
            self.conn.close()
            print("finally")