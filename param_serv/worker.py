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
        meta_rlock,
        db,
        db_rlock,
        server_ip,
        server_port
        ):

        super(self.__class__, self).__init__()
        
        self.conn = None
        self.meta = meta
        self.meta_rlock = meta_rlock
        self.db = db
        self.db_rlock = db_rlock
        self.server_ip = server_ip
        self.server_port = server_port

    def send_param_by_axis_numbers(self, name, axis_numbers, alpha, beta):
        """ Send parameter to server """
        try:
            with self.db[name] as tensor:
                # this action copies the data
                numeric_data = tensor[selector].tobytes("C")
                type_string = str(tensor.dtype)
                shape_string = str(tensor.shape)

        except KeyError, err:
            pwh(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            pwh("client - send_param error :: param of name '{param_name}' doesn't exist. The thread is not crashing.".format(param_name=name))
            pwh(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                
            print_exc()
            return

        query_metadata = {
            "query_id":     query_HEADER_push_param,
            "query_name":   "send_param",
            "param_name":   name,
            "alpha":        alpha,
            "beta":         beta,
            "param_dtype":  type_string,
            "param_shape":  shape_string,
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
    
    def pull_full_param(self, name):
        """ Pull full parameter from server """

        try:
            send_json(self.conn, {
            "query_name": "pull_full_param",
            "query_id" : query_HEADER_pull_full_param,
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

            with self.db[name] as inner:
                init = np.frombuffer(reception_numeric, dtype=reception_json["param_dtype"])
                new_shape = reception_json["param_shape"] # hash map calls are costly
                print("old shape:{old_shape},\nnew shape:{new_shape}"\
                      .format(old_shape=init.shape, new_shape=new_shape)
                      )
                self.db[name].inner = init.reshape(new_shape)

        except Exception, err:
            pwh(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            pwh(">>>>> client - pull_full_param error :: conn.recv failed")
            pwh(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            print_exc()
            return

    def run(self):

        """
        pwh("server_ip: {server_ip} [{server_ip_type}],\nserver_port: {server_port} [{server_port_type}]"\
            .format(
                server_ip=self.server_ip,
                server_ip_type=type(self.server_ip),
                server_port=self.server_port,
                server_port_type=type(self.server_port),
                ))
        """

        self.conn = None
        for i in range(10):
            try:
                self.conn = socket.create_connection((self.server_ip, self.server_port), timeout=20)
                break
            except EnvironmentError, err:
                if err.errno == 61:
                    pwh(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                    pwh(">>>> client - Connection refused.")
                    pwh(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                    time.sleep(1)

                else:
                    pwh(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                    pwh(">>>> client - EXCEPTION: errno: {errno}".format(errno=err.errno))
                    pwh(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                    pwh(format_exc())
                    sys.exit(-1)

        if self.conn:
            state = EmissionThread_state_INIT
            self.db["test"] = Entry(np.zeros((10, 10)))

            # while True:
            for i in range(1):
                if state == EmissionThread_state_INIT:
                    self.pull_full_param("test")
                    with self.db["test"] as inner:
                        pwh("client - This client got back the value : {inner}"
                            .format(inner=str(inner.tolist())))
                    pwh("client - This client is done")
        else:
            pwh("client - WE FAILED")

