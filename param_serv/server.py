#!/usr/bin/env python2
from __future__ import print_function, with_statement, division, generators
from traceback import format_exc
from param_utils import *

class AcceptorThread(threading.Thread):
    def __init__(self, meta, meta_rlock, db, db_rlock):
        super(self.__class__, self).__init__()
        self.meta =                 meta
        self.meta_rlock =           meta_rlock
        self.db =                   db
        self.db_rlock =             db_rlock
        self.sock =                 None


    def bind(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.bind(('', 0))
            self.sock.getsockname()[1]
            self.sock.listen(100)

        except socket.error, s_err:
            if s_err.errno == 48:
                pwh(format_exc())
                return None
            else:
                raise s_err

        return self.sock.getsockname()[1]

    def run(self):
        try:
            while True:
                pwh("Waiting for a connection")
                conn, addr = self.sock.accept()
                pwh("Established new connection.")
                new_thread = ReceptionThread(
                    conn,
                    self.meta,
                    self.meta_rlock,
                    self.db,
                    self.db_rlock)

                new_thread.start()

        finally:
            if self.sock:
                self.sock.close()


class ReceptionThread(threading.Thread):
    def __init__(self, conn, meta, meta_rlock, db, db_rlock):
        super(self.__class__, self).__init__()
        self.conn           =       conn
        self.db             =       db
        self.db_rlock       =       db_rlock
        self.meta           =       meta
        self.meta_rlock     =       meta_rlock
        self.db_insertion_mutex =   threading.RLock()

    def run(self):
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
                    break

                # explicitly cash query_id (hash map lookups are still expensive;
                # we have an interpreter, not a static, aot or jit compiler)
                query_id = data["query_id"]

                if query_id == query_HEADER_pull_full:
                    pwh("server - pull full")
                    param_name = data["name"]

                    with self.db[param_name] as param:
                        numeric_data = param.tobytes()
                        # we copy this very small tuple to not have to keep the lock
                        # on param until the answer is sent
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
                        # we copy this very small tuple to not have to keep the lock
                        # on param until the answer is sent
                        target_shape_str = copy.copy(param.shape)
                        target_dtype_str = str(param.dtype)

                    answer = {
                        "query_id":      query_answer_HEADER_pull_part,
                        "query_name":    "answer_pull_part",
                        "name":          param_name,
                        "dtype":         target_dtype_str,
                        "shape":         target_shape_str,
                        "axis_numbers":  axis_numbers
                    }

                    send_json(self.conn, answer)
                    send_numeric_from_bytes(self.conn, numeric_data)
                    continue
                elif query_id == query_HEADER_push_full:
                    param_name =    data["name"]
                    alpha =         data["alpha"]
                    beta =          data["beta"]

                    numeric_data = receive_numeric(self.conn)

                    with self.db[param_name] as param:
                        numeric_data = numeric_data.reshape(param.shape)
                        numeric_data = numeric_data.astype(param.dtype)
                        param[:] = alpha * param + beta * numeric_data
                    continue
                elif query_id == query_HEADER_push_part:
                    param_name =    data["name"]
                    axis_numbers =  data["axis_numbers"]
                    alpha =         data["alpha"]
                    beta =          data["beta"]
                    shape =         data["shape"]

                    numeric_data = receive_numeric(self.conn)

                    with self.db[param_name] as param:
                        numeric_data = numeric_data.astype(param.dtype).reshape(shape)
                        set_submatrix_from_axis_numbers(
                            param,
                            numeric_data,
                            alpha,
                            beta,
                            axis_numbers)
                    continue
                elif query_id == query_HEADER_push_from_indices:
                    """ we receive the param data, then we receive the indices,
                        then we iterate through the indices and assign the associated
                        values in the db
                    """

                    name = data["name"]
                    _type = data["dtype"]
                    alpha = data["alpha"]
                    beta = data["beta"]

                    indices = receive_numeric(self.conn)
                    numeric_data = receive_numeric(self.conn)
                    indices = indices.astype(int)

                    with self.db[name] as param:
                        numeric_data = numeric_data.astype(_type)
                        for i in indices.shape[0]:
                            index = indices[i, :]
                            param[index] = alpha * param[index] + \
                                beta * numeric_data[i]
                    continue
                elif query_id == query_HEADER_pull_from_indices:
                    """ We receive an array with the indices, allocate the array
                        for the values, iterate through the indices & assign
                        them to the array.

                        We then send the array.
                    """
                    name = data["name"]
                    indices_shape = data["indices_shape"]
                    indices_dtype = data["indices_dtype"]

                    indices = receive_numeric(self.conn).astype(indices_dtype) \
                        .reshape(indices_shape)
                    values = np.empty(shape=indices.shape)

                    with self.db[name] as param:
                        for i in xrange(indices.shape[0]):
                            ind_t = tuple(indices[i, :])
                            values[i, :] = param[ind_t]

                    send_json(self.conn, {
                        "dtype": str(values.dtype),
                        "shape": values.shape,
                    })

                    send_numeric_from_bytes(self.conn, values.tobytes())
                    continue
                elif query_id == query_HEADER_create_if_doesnt_exist:
                    """ So the main reasonning here is that we want this query to finish after
                        the param was initiated to simplify parallel work.

                        All threads block until the insertion is complete, then, all clients will
                        be released very quickly.
                    """
                    name = data["name"]
                    _type = data["dtype"]
                    shape = data["shape"]

                    with self.db_insertion_mutex:
                        if name not in self.db:
                            send_json(self.conn, {"requesting_param": True})
                            param = receive_numeric(self.conn).astype(_type).reshape(shape)
                            self.db[name] = Entry(param)
                            pwh("server - added '%s'" % name)
                        else:
                            send_json(self.conn, {"requesting_param": False})
                    continue
                else:
                    pwh(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                    pwh(">>>> server - Exception: Unsupported query id #%d with "
                        "name %s. closing the socket." % (data["query_id"], data.get("[query_name]",
                        "[Query name not specified]")))
                    pwh(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")

                    with self.meta["exceptions-log"] as exceptions_log:
                        exceptions_log.write("Exception: Unsupported query id. closing the socket.")
                    break
        finally:
            self.conn.close()
            print("The server thread is exiting.")
