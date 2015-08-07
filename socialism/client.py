#!/usr/bin/env python2
from __future__ import print_function, with_statement, division, generators

""" Extremely simple launch script. Should be improved. """
import sys

from socialism.param_serv.param_utils import *

from traceback import format_exc


def pwhcf(param_name=None):
    text = "Client - %s" % caller_name()

    if param_name is not None:
        text += " - {param_name}".format(param_name=param_name)

    pwh(text)

class Client(object):
    def __init__(self):
        pwhcf()
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

    def push_as_part(self, name, axis_numbers, alpha, beta):
        """
        Push matrix to be assigned to a submatrix of the server's parameter.
        This is used with dropout.

        :param name: Name of the param of which to pull a submatrix from
        :param axis_numbers: The axis numbers that compose the submatrix we are pulling
        :param alpha: The linear importance of the server's previous value in the new assignment
        :param beta: The linear importance of the value being sent by the client in the new assignment
        :return: No return value/Always None.
        """
        pwhcf(name)
        try:
            tensor = self._db[name]

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
            "axis_numbers":     axis_numbers
            }

        try:
            send_json(self._conn, query_metadata)
            send_numeric_from_bytes(self._conn, tensor)

        except Exception, err:
            pwh(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            pwh(">>>> client - send_param error :: conn.sendall failed. The thread is not crashing.")
            pwh(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")

            print_exc()
            return

    def push_full(self, name, alpha, beta):
        """
        Push matrix to be assigned to a submatrix of the server's parameter.
        This is used with dropout.

        :param name: Name of the param of which to pull a submatrix from
        :param axis_numbers: The axis numbers that compose the submatrix we are pulling
        :param alpha: The linear importance of the server's previous value in the new assignment
        :param beta: The linear importance of the value being sent by the client in the new assignment
        :return: No return value/Always None.
        """
        pwhcf(name)

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
        """
        Pull part of the full param & assign the value to the contained param.
        This is used with dropout.
        :param name: Name of the param of which to pull a submatrix from
        :param axis_numbers: The axis numbers that compose the submatrix we are pulling
        :return: Nothing; the submatrix that we pull is assigned to an inner parameter.
        """
        pwhcf(name)

        send_json(self._conn, {
            "query_name":   "pull_part",
            "query_id":     query_HEADER_pull_part,
            "name":         name,
            "axis_numbers": axis_numbers,
            })

        numeric = receive_numeric(self._conn)
        self._db[name] = numeric

    def pull_full(self, name):
        """
        Pull full parameter from server

        :param name: Name of the param
        :return: No return value/Always None.
        """
        pwhcf(name)
        assert isinstance(name, str), "Argument 'name' needs to be a string."

        send_json(self._conn, {
            "query_name":   "pull_full",
            "query_id":    query_HEADER_pull_full,
            "name":         name,
        })

        # ignore the json
        receive_json(self._conn)
        reception_numeric = receive_numeric(self._conn)
        reception_numeric.flags.writeable = True

        self._db[name] = reception_numeric

    def push_from_indices(self, name, indices, alpha, beta):
        """
        Push values to the server by specifying each of their indices.

        :param name: Name of the parameter that we're trying to push
        :param indices: List of tuples with the indices of the values that we're trying to push
        :param alpha: Float for the calculation of the final value on the server
        :param beta: Float for the calculation of the final value on the server
        :return: No return value/Always None.
        """
        pwhcf(name)
        assert isinstance(name, str), "Argument 'name' needs to be a string."
        assert isinstance(indices, list) or isinstance(indices, tuple), "Argument 'indicies' needs to be a list of tuples or a tuple of tuples."

        # Here we try to force the alpha and beta arguments to floats
        alpha = float(alpha)
        beta = float(beta)

        np_indices = np.array(indices)
        values = self._db[name][np_indices.T.tolist()]
        send_json(self._conn, {
            "query_id":         query_HEADER_push_from_indices,
            "name":             name,
            "beta":             beta,
            "alpha":            alpha
        })

        send_numeric_from_bytes(self._conn, np_indices)
        send_numeric_from_bytes(self._conn, values)

    def pull_from_indices(self, name, indices):
        """
        Pull values from the server, by specifying the index of each value
        This function probably shouldn't exist.
        The other possibility is to have this verify if it makes squares or something.

        :param name: Name of the param
        :param indices: Tuple of tuple or list of tuples with the indices of the values to be requested from the server
        :return: No return value/Always None.
        """
        pwhcf(name)
        assert False, "TODO."

        assert not isinstance(name, str), "Argument 'name' needs to be a valid string."
        assert not isinstance(indices, list) \
               and not isinstance(indices, tuple), \
            "Argument 'indices' needs to be a list or a tuple"


        # they need to be all the same shape
        first = len(indices[0])
        assert all([len(t) == first for t in indices]), "index tuples need to all have the same len"

        print(indices)
        np_indices = np.array(indices).T

        send_json(self._conn, {
            "query_id":         query_HEADER_pull_from_indices,
            "name":             name
        })

        send_numeric_from_bytes(self._conn, np_indices)
        values = receive_numeric(self._conn)
        param = self._db[name]

        """
        for i in xrange(np_indices.shape[0]):
            index = np_indices[i, :]
            param[index] = numeric_data[i]
        """

        param[np_indices.tolist()] = values[:]

    def create_once(self, name, arr):
        """
        Ask the server to create an entry in its db with this name if it doesn't already exist.
        Assign the value in arr if it doesn't already exist.

        :param name: Name of the param
        :param arr: value of the param
        :return: Nothing/Always None.
        """
        pwhcf(name)
        assert name is not None, "Argument 'name' cannot be None."
        assert arr is not None, "Argument 'arr' cannot be None."


        send_json(self._conn, {
            "query_id": query_HEADER_create_if_doesnt_exist,
            "name":     name,
        })

        test = receive_json(self._conn)

        if test["requesting_param"]:
            send_numeric_from_bytes(self._conn, arr)
            self._db[name] = arr
        else:
            self._db[name] = receive_numeric(self._conn)

    def server_save_to_hdf5(self, path):
        """
        Ask the server to save his db in the hdf5 format to the specified path.

        :param path: Path on the server where we want it to save its database
        :return: No return value/Always None.
        """
        pwhcf()

        send_json(self._conn, {
            "query_id": query_HEADER_save_all_to_hdf5,
            "path": path,
            })

    def __getitem__(self, item):
        return self._db[item]

    def __setitem__(self, name, item):
        # not sure about this yet
        if name not in self._db:
            self.create_once(name, item)
            return

        self._db.__setitem__(name, item)

    def get(self, name):
        return self._db[name]