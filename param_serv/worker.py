#!/usr/bin/env python2
""" Client worker. """
from __future__ import print_function, with_statement, division, generators

import numpy as np
import sys
from traceback import format_exc
from param_serv.param_utils import *

class ConnectorThread(threading.Thread):
    """ This is the client worker thread; it's the object
    that sends and receives the data to and form the server """
    def __init__(
        self,
        meta,
        db,
        server_ip,
        server_port
        ):

        super(self.__class__, self).__init__()
        self.conn = None
        self.meta = meta
        self.db = db
        self.server_ip = server_ip
        self.server_port = server_port

    def push_part(self, name, axis_numbers, alpha, beta):
        print("worker.push_part")
        try:
            tensor = self.db[name]
            # this action copies the data
            transformed_view = from_axis_numbers(tensor, axis_numbers)
            numeric_data = transformed_view.tobytes()
            type_string = str(transformed_view.dtype)
            sub_param_shape_string = str(transformed_view.shape)

        except KeyError, err:
            pwh(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            pwh("client - send_param error :: param of name '{param_name}' doesn't exist. The thread is not crashing.".format(param_name=name))
            pwh(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                
            print_exc()
            return

        query_metadata = {
            "query_id":         query_HEADER_push_part,
            "query_name":       "push_part",
            "param_name":       name,
            "alpha":            alpha,
            "beta":             beta,
            "param_type":       type_string,
            "sub_param_shape":  sub_param_shape_string,
            "axis_numbers":     axis_numbers
            }

        try:
            send_json(self.conn, query_metadata)
            send_numeric_from_bytes(self.conn, numeric_data)

        except Exception, err:
            pwh(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            pwh(">>>> client - send_param error :: conn.sendall failed. The thread is not crashing.")
            pwh(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")

            print_exc()
            return

    def push_full(self, name, alpha, beta):
        print("worker.pull_full")

        send_json(self.conn, {
            "query_name": "push_full",
            "query_id": query_HEADER_push_full,
            "param_name": name,
            "alpha": alpha,
            "beta": beta
            })

        send_numeric_from_bytes(self.conn, self.db[name].tobytes())

    def pull_part(self, name, alpha, beta):
        #TODO: far from functionnal

        print("worker.pull_part")
        send_json(self.conn, {
            "query_name": "pull_part",
            "query_id": query_HEADER_pull_part,
            "param_name": name,
            "alpha": alpha,
            "beta": beta
            })

        send_numeric_from_bytes(self.conn, self.db[name].tobytes())

    def pull_full(self, name):
        """ Pull full parameter from server """
        print("worker.pull_full")
        try:
            send_json(self.conn, {
            "query_name": "pull_full",
            "query_id" : query_HEADER_pull_full,
            "param_name": name,
            })

        except Exception, err:
            pwh(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            pwh(">>>>> client - send_param error :: conn.sendall failed. The thread is not crashing. ")
            pwh(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            print_exc()
            return

        try:
            # ignore the json header bytes
            reception_json = receive_json(self.conn)
            reception_numeric = receive_numeric(self.conn)

            init = np.frombuffer(reception_numeric, dtype=reception_json["param_dtype"])
            new_shape = reception_json["param_shape"] # hash map calls are costly
            self.db[name] = init.reshape(new_shape)

        except Exception, err:
            pwh(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            pwh(">>>>> client - pull_full_param error :: conn.recv failed")
            pwh(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            print_exc()
            return

    def run(self):

        self.conn = None
        for i in range(3):
            try:
                self.conn = socket.create_connection((self.server_ip, self.server_port), timeout=20)
                break

            except EnvironmentError, err:
                if err.errno == 61:
                    pwh(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                    pwh(">>>> client - Connection refused.")
                    pwh(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")

                else:
                    pwh(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                    pwh(">>>> client - EXCEPTION: errno: {errno}".format(errno=err.errno))
                    pwh(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                    pwh(format_exc())
                    sys.exit(-1)

        self.db["test"] = np.zeros((10, 10))
