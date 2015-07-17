#!/usr/bin/env python2
from __future__ import print_function, with_statement, division, generators

""" Extremely simple launch script. Should be improved. """
import sys

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

    def push_part(self, name, axis_numbers, alpha, beta):
        print("worker.push_part")
        try:
            tensor = self._db[name]
            # this action copies the data
            transformed_view = get_submatrix_from_axis_numbers(tensor, axis_numbers)
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
            "name":             name,
            "alpha":            alpha,
            "beta":             beta,
            "dtype":            type_string,
            "sub_param_shape":  sub_param_shape_string,
            "axis_numbers":     axis_numbers,
            "shape":            transformed_view.shape
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
            "query_name":   "push_full",
            "query_id":     query_HEADER_push_full,
            "name":         name,
            "alpha":        alpha,
            "beta":         beta
            })

        send_numeric_from_bytes(
            self._conn,
            self._db[name].tobytes())

    def pull_part(self, name, axis_numbers):
        #TODO: far from functionnal

        send_json(self._conn, {
            "query_name":   "pull_part",
            "query_id":     query_HEADER_pull_part,
            "name":         name,
            "axis_numbers": axis_numbers,
            })

        meta = receive_json(self._conn)
        shape = [len(x) for x in axis_numbers] # len(x): number of axises in a dimension
        numeric = receive_numeric(self._conn).reshape(shape)

        set_submatrix_from_axis_numbers(self._db[name], numeric, 0, 1, axis_numbers)

    def pull_full(self, name):
        """ Pull full parameter from server """
        send_json(self._conn, {
        "query_name":   "pull_full",
        "query_id" :    query_HEADER_pull_full,
        "name":         name,
        })

        # ignore the json header bytes
        json_data = receive_json(self._conn)
        reception_numeric = receive_numeric(self._conn)

        param_dtype = json_data["dtype"]
        param_shape = json_data["shape"]

        init = np.frombuffer(reception_numeric, dtype=param_dtype)
        init.flags.writeable = True
        self._db[name] = init.reshape(param_shape)

    def push_from_indices(self, name, indices, alpha, beta):
        np_indices = np.array(indices)
        values = np.zeros(shape=np_indices.shape)

        with self._db as param:
            for i in xrange(np_indices.shape[0]):
                values[i, :] = param[np_indices[i, :]]

        send_json({
            "query_id":         query_HEADER_push_from_indices,
            "name":             name,
            "shape":            values.shape,
            "indices_shape":    indices.shape,
            "indices_dtype":    str(indices.dtype),
            "dtype":            str(values.dtype),
            "beta":             beta,
            "alpha":            alpha
        })

        send_numeric_from_bytes(np_indices)
        send_numeric_from_bytes(values)

    def pull_from_indices(self, name, indices):

        # they need to be all the same shape
        first = len(indices[0])
        assert all([len(t) == first for t in indices]), "index tuples need to all have the same len"

        np_indices = np.array(indices)
        # print(np_indices)

        send_json(self._conn, {
            "query_id":         query_HEADER_pull_from_indices,
            "name":             name,
            "indices_shape":    np_indices.shape,
            "indices_dtype":    str(np_indices.dtype)
        })

        send_numeric_from_bytes(self._conn, np_indices.tobytes())
        data = receive_json(self._conn)
        values = receive_numeric(self._conn)

        param = self._db[name]
        np_indices = np_indices.astype(int)
        numeric_data = values.astype(data["dtype"])

        """
        for i in xrange(np_indices.shape[0]):
            index = np_indices[i, :]
            param[index] = numeric_data[i]
        """

        print (numeric_data[:])

        param[np_indices] = numeric_data[:]


    def create_if_doesnt_exist(self, name, arr=None):
        if arr is not None:
            self._db[name] = arr

        else:
            arr = self._db[name]

        send_json(self._conn, {
            "query_id": query_HEADER_create_if_doesnt_exist,
            "name":     name,
            "shape":    arr.shape,
            "dtype":    str(arr.dtype)
        })

        test = receive_json(self._conn)

        if test["requesting_param"]:
            send_numeric_from_bytes(self._conn, arr.tobytes())

    def __getitem__(self, item):
        return self._db[item]

    def __setitem__(self, *vargs,  **kwargs):
        self._db.__setitem__(*vargs, **kwargs)

    def get(self, name):
        return self._db[name]