#!/usr/bin/env python2
from __future__ import print_function, with_statement, division, generators

""" Extremely simple launch script. Should be improved. """
import os, sys, re, threading, socket, time
import subprocess as sp
import param_serv.server


from param_serv.param_utils import *

from traceback import format_exc

class Client(object):
    def __init__(self):
        # we minimise the number of hash map lookups by saving refs to values used more than once
        self._server_ip = os.environ["SOCIALISM_server_ip"]
        self._server_port = os.environ["SOCIALISM_server_port"]
        self._db = {}

        self._conn = None
        for i in range(3):
            try:
                self._conn = socket.create_connection((self._server_ip, self._server_port), timeout=20)
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

        self._db["test"] = np.zeros((10, 10))

    def push_part(self, name, axis_numbers, alpha, beta):
        print("worker.push_part")
        try:
            tensor = self._db[name]
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
            "name":       name,
            "alpha":            alpha,
            "beta":             beta,
            "dtype":       type_string,
            "sub_param_shape":  sub_param_shape_string,
            "axis_numbers":     axis_numbers
            }

        try:
            send_json(self._conn, query_metadata)
            send_numeric_from_bytes(self._conn, numeric_data)

        except Exception, err:
            pwh(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            pwh(">>>> client - send_param error :: conn.sendall failed. The thread is not crashing.")
            pwh(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")

            print_exc()
            return

    def push_full(self, name, alpha, beta):
        print("worker.pull_full")

        send_json(self._conn, {
            "query_name": "push_full",
            "query_id": query_HEADER_push_full,
            "name": name,
            "alpha": alpha,
            "beta": beta,
            "dtype": str(self._db[name].dtype),
            "shape": self._db[name].shape
            })

        send_numeric_from_bytes(self._conn, self._db[name].tobytes())

    def pull_part(self, name, alpha, beta):
        #TODO: far from functionnal

        print("worker.pull_part")
        send_json(self._conn, {
            "query_name": "pull_part",
            "query_id": query_HEADER_pull_part,
            "name": name,
            "alpha": alpha,
            "beta": beta
            })

        send_numeric_from_bytes(self._conn, self._db[name].tobytes())

    def pull_full(self, name):
        """ Pull full parameter from server """
        print("worker.pull_full")
        try:
            send_json(self._conn, {
            "query_name": "pull_full",
            "query_id" : query_HEADER_pull_full,
            "name": name,
            })

        except Exception, err:
            pwh(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            pwh(">>>>> client - send_param error :: conn.sendall failed. The thread is not crashing. ")
            pwh(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            print_exc()
            return

        try:
            # ignore the json header bytes
            reception_json = receive_json(self._conn)
            reception_numeric = receive_numeric(self._conn)

            init = np.frombuffer(reception_numeric, dtype=reception_json["dtype"])
            new_shape = reception_json["shape"] # hash map calls are costly
            self._db[name] = init.reshape(new_shape)

        except Exception, err:
            pwh(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            pwh(">>>>> client - pull_full_param error :: conn.recv failed")
            pwh(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            print_exc()
            return

    def __getitem__(self, item):
        return self._db[item]

    def __setitem__(self, key, value):
        self._db[key] = value

    def get(self, name):
        return self._db[name]