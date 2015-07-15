#!/usr/bin/env python2
from __future__ import print_function, with_statement, division, generators
import copy
from traceback import format_exc

import numpy as np

from param_utils import *


class AcceptorThread(threading.Thread):
    def __init__(self, meta, meta_rlock, db, db_rlock):
        super(self.__class__, self).__init__()
        self.meta = meta
        self.meta_rlock = meta_rlock
        self.db = db
        db["test"] = Entry(np.ones([10, 10]))
        self.db_rlock = db_rlock
        self.sock = None

    def bind(self):
        try:

            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.bind(('', 0))
            self.sock.getsockname()[1]
            self.sock.listen(100)

        except socket.error, serr:
            if serr.errno == 48:
                pwh(format_exc())
                return None
            else:
                raise serr

        return self.sock.getsockname()[1]


    def run(self):
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

                    else:
                        pwh(">>>> server - recv failed; unknown error of no {errno}".format(errno=serr.errno))
                        raise serr

                    return

                # To make checking less verbose
                if "query_id" not in data:
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
                        "name":        param_name,
                        "shape":       target_shape_str,
                        "dtype":       target_dtype_str
                    }

                    send_json(self.conn, answer)
                    print(">>>>> server - numeric_data size: %i" % len(numeric_data))
                    send_numeric_from_bytes(self.conn, numeric_data)

                    continue

                elif query_id == query_HEADER_pull_part:
                    param_name = data["name"]
                    axis_numbers = data["axis_numbers"]

                    with self.db[param_name] as param:
                        reshaped = get_submatrix_from_axis_numbers(param, axis_numbers)
                        numeric_data = reshaped.tobytes()
                        target_shape_str = str(param.shape)
                        target_dtype_str = str(param.dtype)

                    answer = {
                        "query_id":      query_answer_HEADER_pull_part,
                        "query_name":    "answer_pull_part",
                        "name":          param_name,
                        "dtype":         target_dtype_str,
                        "shape":         target_shape_str,
                        "axis_numbers": axis_numbers
                    }

                    send_json(self.conn, answer)
                    send_numeric_from_bytes(self.conn, numeric_data)

                    continue

                elif query_id == query_HEADER_pull_from_indices:
                    param_name = data["name"]
                    indices = receive_numeric(self.conn)
                    with self.db[param_name] as param:
                        pack = [param.__getitem__(*x) for x in indices]

                    answer = {
                        "query_id":      query_answer_HEADER_pull_part,
                        "query_name":    "answer_pull_part",
                        "name":          param_name,
                        "dtype":         target_dtype_str,
                        "shape":         target_shape_str,
                        "axis_numbers": axis_numbers
                    }

                    send_json(self.conn, answer)
                    send_numeric_from_bytes(self.conn, numeric_data)

                    continue
                elif query_id == query_HEADER_push_full:

                    param_name = data["name"]
                    numeric_data = receive_numeric(self.conn)

                    with self.db[param_name] as param:
                        numeric_data = numeric_data.reshape(param.shape)
                        numeric_data = numeric_data.astype(param.dtype)
                        param[:] = data["alpha"] * param + \
                            data["beta"] * numeric_data

                    continue
                elif query_id == query_HEADER_push_part:
                    param_name = data["name"]
                    numeric_data = receive_numeric(self.conn)

                    with self.db[param_name] as param:
                        numeric_data = numeric_data.astype(param.dtype).reshape(data["shape"])
                        set_submatrix_from_axis_numbers(param, numeric_data, data["alpha"], data["beta"], data["axis_numbers"])
                    continue

                elif query_id == query_HEADER_push_from_indices:
                    param_name = data["name"]
                    indices = receive_numeric(self.conn)
                    numeric_data = receive_numeric(self.conn)

                    with self.db[param_name] as param:
                        indices = indices.astype(int)
                        numeric_data = numeric_data.astype(data["dtype"])
                        for i in indices.shape[0]:
                            index = indices[i, :]
                            param[index] = data["alpha"] * param[index] + data["beta"] * numeric_data[i]
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