from __future__ import print_function, with_statement, division, generators
__author__ = 'jules'

from param_utils import *

def client_send_unit(name, param, json, indices):
    np_indices = np.array(indices)
    values = np.zeros(shape = np_indices.shape)
    for i in xrange(np_indices.shape[0]):
        values[i, :] = param[np_indices[i, :]]

    send_json({
        "query_id": query_HEADER_push_from_indices,
        "name": name,
        "shape": values.shape,
        "indices_shape": indices.shape,
        "indices_dtype": str(indices.dtype),
        "dtype": str(values.dtype),
        "beta": beta,
        "alpha": alpha
    })

    send_numeric_from_bytes(np_indices)
    send_numeric_from_bytes(values)

def server_send_unit(self):
    indices = receive_numeric(self.conn).astype(data["indices_dtype"]).reshape(data["indices_shape"])
    values = receive_numeric(self.conn).astype(data["dtype"]).reshape(data["shape"])

    for i in xrange(indices.shape[0]):
        ind_t = tuple(indices[i, :])
        param[ind_t] = data["alpha"] * param[ind_t] + data["beta"] * values[i, :]