from __future__ import print_function, with_statement, division, generators
import socket
import json
import struct
import threading
import os
import time
import datetime
from traceback import print_exc
from itertools import product

import numpy as np

from headers import *


def get_submatrix_from_axis_numbers(arr, axis_numbers):
    temp = np.array([arr[x] for x in product(*axis_numbers)])
    return temp.reshape([len(x) for x in axis_numbers])


def set_submatrix_from_axis_numbers(param, addition, alpha, beta, axis_numbers):
    indices = np.array(list(product(* axis_numbers)))
    new_shape = [len(x) for x in axis_numbers] + [2]
    indices = indices.reshape(tuple(new_shape))

    ranges_of_positions_in_indices_table = [range(len(x)) for x in axis_numbers]

    possible_positions_in_indices_table = list(product(*ranges_of_positions_in_indices_table))

    for position in possible_positions_in_indices_table:
        tind = tuple(indices[position])
        a = alpha * param[tind]
        b = beta * addition[position]
        param[tind] = a + b


def our_ip():
    return socket.gethostbyname(socket.gethostname())


def insert_tabs(text):
    return "\t" + text.replace("\n", "\n\t")


def get_tod():
    return time.strftime("%H:%M:%S", time.gmtime())


def header():
    return "tod::{tod} - pid::{pid}".format(tod=get_tod(), pid=os.getpid())


# print_with_header
def pwh(text):
    print("{header}: {text}".format(
        header=header(), 
        text=text))


class Entry(object):
    def __init__(self, val):
        self.inner = val
        self.rlock = threading.RLock()
    
    def __enter__(self):
        self.rlock.acquire()    
        return self.inner

    def __exit__(self, _type, value, traceback):
        self.rlock.release()

"""
def view_from_slice(tensor, _slice):
    assert False, "Dead code."

    assert False, "Needs rebuilding. don't use."

    formatted_slice = []
    for i in xrange(len(slice.shape)):
        formatted_slice.append([j for j in xrange(_slice[i])])

    return tensor.__getitem__(formatted_slice)
"""


def now_milliseconds():
    now = datetime.datetime.now()
    return (now.days * 24. * 60. * 60. + now.seconds) * 1000. + now.microseconds / 1000.


def send_numeric_from_bytes(conn, array):
    send_json(conn, {
        "shape": array.shape,
        "dtype": str(array.dtype)
    })
    array_bytes = array.tobytes()
    bytes = struct.pack("ii%ds" % len(array_bytes), HEADER_NUMERIC, len(array_bytes), array_bytes)
    conn.sendall(bytes)

def receive_numeric(conn):
    meta = receive_json(conn)
    header = struct.unpack("i", brecv(conn, struct.calcsize("i")))[0]
    data_size = struct.unpack("i", brecv(conn, struct.calcsize("i")))[0]
    data = brecv(conn, data_size)
    final_data = np.frombuffer(data, dtype=meta["dtype"]).reshape(meta["shape"])
    final_data.flags.writeable = True
    return final_data


def send_json(conn, dict_to_transform):
    data = json.dumps(dict_to_transform)
    bytes = struct.pack("ii%ds" % len(data),  HEADER_JSON,    len(data),  data)
    conn.sendall(bytes)


def server_compatibility_check(meta, meta_rlock, query):
    with meta["server-queries"] as server_queries:
        test = query in server_queries

    return test    


def brecv(conn, size):
    # socket.MSG_WAITALL doesnt work on all platforms
    buff = conn.recv(size, socket.MSG_WAITALL)
    while len(buff) < size:
        temp = conn.recv(size - len(buff), socket.MSG_WAITALL)
        buff += temp

    assert len(buff) == size
    return buff


def receive_json(conn):
    header = struct.unpack("i", brecv(conn, struct.calcsize("i")))[0]
    assert header == HEADER_JSON, "expected {header_json}, got {header}".format(header_json=HEADER_JSON, header=header)
    number_of_bytes_to_receive = struct.unpack("i", brecv(conn, struct.calcsize("i")))[0]
    str_data = brecv(conn, number_of_bytes_to_receive)
    raw = struct.unpack("%ds" % number_of_bytes_to_receive, str_data)[0]
    try:
        data = json.loads(raw)
        
    except ValueError, err:
        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        print(">>>>> json conversion failed - Raw: %s" % raw)
        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        print_exc()
        exit(-1)

    return data
