#!/usr/bin/env python2
from __future__ import print_function, with_statement, division, generators
import socket, sys, os, threading
from traceback import format_exc


from legion.core.param_serv.param_utils import *
from legion.core.checkpoint_hdf5 import server_save_db_to_hdf5

class ReceptionThread(threading.Thread):
    """
    This is the server's main client interaction loop thread object.
    Each connection to a client has one of these.

    :return: Nothing.
    """

    def __init__(self, conn, meta, meta_rlock, db, db_rlock):
        super(self.__class__, self).__init__()
        self.conn               = conn
        self.db                 = db
        self.db_rlock           = db_rlock
        self.meta               = meta
        self.meta_rlock         = meta_rlock
        self.db_insertion_mutex = threading.RLock()

    def pwhs(self, state, param_name = None, extra = None):
        """
        Prints the date, the pid, the fact that this is the server, and the name of current state.
        :return: No return value.
        """
        text = "Server - client hash '{client_pid}' - {state}".format(client_pid=self.conn.__hash__(), state=state)
        if param_name is not None:
            text += " - " + param_name

        if extra is not None:
            text += " - " + extra

        pwh(text)


    def run(self):
        """
        This is the server's main client interaction loop. Each connection to a client has one of these.
        :return: Nothing.
        """
        try:
            while True:
                try:
                    data = receive_json(self.conn)
                except socket.error, s_err:
                    if s_err.errno == 104:
                        pwh(">>>> server - The client closed the connection.")
                    else:
                        pwh(">>>> server - recv failed; unknown error of no {errno}"
                            .format(errno=s_err.errno))
                        raise s_err
                    return

                if "query_id" not in data:

                    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                    print(">>>> server - Server received a query without a query id. "
                          "Killing connection and thread.")
                    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                    raise

                # explicitly cash query_id (hash map lookups are still expensive;
                # we have an interpreter, not a static, aot or jit compiler)
                query_id = data["query_id"]

                if query_id == query_HEADER_pull_full:
                    """
                    The client wants to pull the full param from the server.
                    """
                    param_name = data["name"]
                    self.pwhs("pull_full", param_name)
                    assert param_name in self.db, "Bad param name."

                    answer = {
                        "query_id":    query_answer_HEADER_pull_full,
                        "query_name":  "answer_pull_full",
                        "name":        param_name,
                    }
                    send_json(self.conn, answer)
                    with self.db[param_name] as param:
                        send_numeric_from_bytes(self.conn, param)
                    continue

                elif query_id == query_HEADER_pull_part:
                    """
                    The client wants to pull part of the param, from the axis numbers.
                    """
                    param_name = data["name"]
                    self.pwhs("pull_part", param_name)
                    assert param_name in self.db, "Bad param name."

                    axis_numbers = data["axis_numbers"]
                    with self.db[param_name] as param:
                        reshaped = get_submatrix_from_axis_numbers(param, axis_numbers)
                        send_numeric_from_bytes(self.conn, reshaped)
                    continue

                elif query_id == query_HEADER_push_full:
                    """
                    The client is trying to push his full param.
                    """
                    param_name = data["name"]
                    self.pwhs("push_full", param_name)
                    assert param_name in self.db, "Bad param name."

                    alpha =         data["alpha"]
                    beta =          data["beta"]
                    numeric_data = receive_numeric(self.conn)

                    with self.db[param_name] as param:
                        param[:] = alpha * param + beta * numeric_data
                    continue

                elif query_id == query_HEADER_push_part:
                    """
                    The client is trying to push part of a param, by axis numbers.
                    """
                    param_name =    data["name"]
                    self.pwhs("push_part", param_name)
                    assert param_name in self.db, "Bad param name."

                    axis_numbers =  data["axis_numbers"]
                    alpha =         data["alpha"]
                    beta =          data["beta"]

                    numeric_data = receive_numeric(self.conn)

                    with self.db[param_name] as param:
                        numeric_data = numeric_data
                        set_submatrix_from_axis_numbers(
                            param,
                            numeric_data,
                            alpha,
                            beta,
                            axis_numbers)

                    continue

                elif query_id == query_HEADER_push_from_indices:
                    """
                    We receive the param data, then we receive the indices,
                    then we iterate through the indices and assign the associated
                    values in the db
                    """
                    param_name = data["name"]
                    self.pwhs("push_from_indices", param_name)
                    assert param_name in self.db, "Bad param name."

                    alpha = data["alpha"]
                    beta = data["beta"]

                    indices = receive_numeric(self.conn)
                    numeric_data = receive_numeric(self.conn)
                    formatted_indices = indices.T.tolist()

                    with self.db[param_name] as param:
                        param[formatted_indices] = alpha * param[formatted_indices] + beta * numeric_data[:]
                    continue

                elif query_id == query_HEADER_pull_from_indices:
                    """
                    We receive an array with the indices, allocate the array
                    for the values, iterate through the indices & assign
                    them to the array.

                    We then send the array.
                    """
                    param_name = data["name"]
                    self.pwhs("pull_from_indices", param_name)
                    assert param_name in self.db, "Bad param name."

                    indices = receive_numeric(self.conn)

                    with self.db[param_name] as param:
                        send_numeric_from_bytes(self.conn, param[indices.tolist()])

                    continue

                elif query_id == query_HEADER_create_if_doesnt_exist:
                    """
                    All threads block until the insertion is complete, then, all clients except the first one
                    receive a copy of the array that got the lock the first, so they all have the same array
                    """
                    param_name = data["name"]
                    self.pwhs("create_if_doesnt_exist", param_name, "Entry")

                    with self.db_insertion_mutex:
                        if param_name not in self.db:

                            send_json(self.conn, {"requesting_param": True})
                            param = receive_numeric(self.conn)
                            self.pwhs("create_if_doesnt_exist", param_name, "Creating. Shape = {shape}".format(shape=param.shape))
                            self.db[param_name] = Entry(param)
                            not_requesting = False

                        # We don't need to keep this mutex to sent the arr back
                        else:
                            not_requesting = True

                    if not_requesting:
                        send_json(self.conn, {"requesting_param": False})
                        self.pwhs("create_if_doesnt_exist", param_name, "Was already created.")
                        # This is an atomic operation; we are only reading.
                        send_numeric_from_bytes(self.conn, self.db[param_name].inner)

                    continue

                elif query_id == query_HEADER_save_all_to_hdf5:
                    """
                    Ask the server to save its database to hdf5.
                    """
                    self.pwhs("save_all_to_hdf5")
                    server_save_db_to_hdf5(data["path"], self.db)
                    continue

                else:
                    from textwrap import dedent
                    # Making multiline text not ugly in
                    text = ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n" \
                           "Server - Exception: Unsupported query id #{query_id} with name {query_name}.\n" \
                           "Closing the socket.\n" \
                           ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n" \
                           .format(query_id  =data["query_id"],
                                   query_name=data.get("query_name", "[Query name not specified]")
                                   )

                    pwh(text)
                    raise RuntimeError(text)

        finally:
            self.conn.close()
