from __future__ import print_function, with_statement, division, generators, absolute_import
""" In here you will find various utility functions mostly used by the param_serv, but not exclusively so.
    Very helpful description, I know. """

import socket, struct, threading, os, time, datetime
import ujson
from traceback import print_exc
from itertools import product
import numpy as np

from socialism.param_serv.headers import *

import inspect

cython_init = "don't remove this."

def f_name():
    """
    Return the caller function's name. Only used for quick logging.
    """
    return inspect.currentframe().f_back.f_code.co_name


def caller_name():
    """
    Display the caller function's caller function's name. Only used for quick logging.
    """
    return inspect.currentframe().f_back.f_back.f_code.co_name


def get_submatrix_from_axis_numbers(arr, axis_numbers):
    """
    Meant for the push part and the pull part functions.
    Return the submatrix from the array indices.
    ...
    This needs further testing.
    """
    temp = np.array([arr[x] for x in product(*axis_numbers)])
    return temp.reshape([len(x) for x in axis_numbers])


def set_submatrix_from_axis_numbers(param, addition, alpha, beta, axis_numbers):
    """
    Meant for the push part and the pull part functions.
    Assign to a matrix's submatrix that corresponds to the axis_numbers.
    """

    # This is extremely unefficient.
    # Generate the individual indices.

    local_indices = np.asarray(list(product(*[range(len(x)) for x in axis_numbers])))
    indices_server = np.asarray(list(product(*axis_numbers)))

    for i in range(indices_server.shape[0]):
        a = alpha * param[tuple(indices_server[i, :])]
        b = beta * addition[tuple(local_indices[i, :])]
        param[tuple(indices_server[i, :])] = a + b


def our_ip():
    """
    Fairly straightforward.
    """
    return socket.gethostbyname(socket.gethostname())

def insert_tabs(text):
    """
    Inserts tabs at the beginning of every line of the passed text.
    Meant to help with the formatting of text meant for logging and exceptions.
    """
    return "\t" + text.replace("\n", "\n\t")


def get_tod():
    """
    Returns the time of day.
    """
    return time.strftime("%H:%M:%S", time.gmtime())


def header():
    return "tod::{tod} - pid::{pid}".format(tod=get_tod(), pid=os.getpid())


# print_with_header
def pwh(text):
    """
    Print with header. Small custom print function with extra information.
    """

    print("{header}: {text}".format(
        header=header(), 
        text=text))


class Entry(object):
    """
    This is the main unit of the database.
    """
    def __init__(self, val):
        self.inner = val
        self.rlock = threading.RLock()
    
    def __enter__(self):
        self.rlock.acquire()    
        return self.inner

    def __exit__(self, _type, value, traceback):
        self.rlock.release()


def now_milliseconds():
    """
    :return: The number of milliseconds since the epoch
    """
    now = datetime.datetime.now()
    return (now.days * 24. * 60. * 60. + now.seconds) * 1000. + now.microseconds / 1000.


def send_numeric_from_bytes(conn, array):
    """
    Sends a numeric numpy array on the connection.
    Uses json for the dtype and shape, and uses straight binary for the array itself.

    :param conn: The connection object
    :param array: A numeric array
    :return: Nothing.
    """
    assert isinstance(array, np.ndarray), "Expected an array of type 'ndarray'. Got an object of type '{type}' instead.".format(type=type(array))
    send_json(conn, {
        "shape": array.shape,
        "dtype": str(array.dtype)
    })
    array_bytes = array.tobytes()
    bytes = struct.pack("ii%ds" % len(array_bytes), HEADER_NUMERIC, len(array_bytes), array_bytes)
    conn.sendall(bytes)


def receive_numeric(conn):
    """
    The other side of the 'send_numeric_from_bytes'. Receives the json metadata, then receives the bytes, then
    reshapes the array and returns it.

    :param conn: The connection object
    :return: The resulting numpy array.
    """
    meta = receive_json(conn)
    header = struct.unpack("i", brecv(conn, struct.calcsize("i")))[0]
    data_size = struct.unpack("i", brecv(conn, struct.calcsize("i")))[0]
    data = brecv(conn, data_size)
    final_data = np.frombuffer(data, dtype=meta["dtype"]).reshape(meta["shape"])
    final_data.flags.writeable = True
    return final_data


def send_json(conn, dict_to_transform):
    """
    Takes a compatible python dictionary, converts it to json, and sends it over the connection.
    :param conn: The connection object.
    :param dict_to_transform: the dictionary to build json from.
    :return: Nothing.
    """
    data = ujson.dumps(dict_to_transform)
    bytes = struct.pack("ii%ds" % len(data),  HEADER_JSON,    len(data),  data)
    conn.sendall(bytes)


def receive_json(conn):
    """
    Receive a json object from a connexion, and convert it to a python dict.
    :param conn: The connection object.
    :return: The python dict build from the received json.
    """
    header = struct.unpack("i", brecv(conn, struct.calcsize("i")))[0]
    assert header == HEADER_JSON, "expected {header_json}, got {header}".format(header_json=HEADER_JSON, header=header)
    number_of_bytes_to_receive = struct.unpack("i", brecv(conn, struct.calcsize("i")))[0]
    str_data = brecv(conn, number_of_bytes_to_receive)
    raw = struct.unpack("%ds" % number_of_bytes_to_receive, str_data)[0]
    try:
        data = ujson.loads(raw)

    except ValueError, err:
        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        print(">>>>> json conversion failed - Raw: %s" % raw)
        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        print_exc()
        exit(-1)

    return data


def brecv(conn, size):
    """
    Blocking reception of given amount of bytes.
    :param conn: the connection object.
    :param size: The expected number of bytes.
    :return: The received buffer.
    """
    # socket.MSG_WAITALL doesnt work on all platforms
    buff = conn.recv(size, socket.MSG_WAITALL)

    while len(buff) < size:
        temp = conn.recv(size - len(buff), socket.MSG_WAITALL)

        # If len(temp) == 0, then the connection has closed.
        if len(temp) == 0:
            # This closes the thread.
            exit(0)

        buff += temp

    assert len(buff) == size
    return buff
