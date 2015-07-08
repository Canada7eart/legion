from __future__ import print_function, with_statement, division, generators
import socket, json, struct
import threading
import sys, os, re, argparse, copy, time, datetime
from headers import *

def our_ip():
   return socket.gethostbyname(socket.gethostname())

def insert_tabs(text):
    return "\t" + text.replace("\n","\n\t")

def getTOD():
    return time.strftime("%H:%M:%S", time.gmtime())

def header():
    return "PBS_NODENUM#%s - %s" % (getTOD(), os.environ["PBS_NODENUM"], )

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


def view_from_slice(tensor, _slice):
    """
    TODO:: Don't actually use this code, lol. 
    I'm 100%% sure there is a better way to do this. """

    assert False, "Needs rebuilding. don't use."

    formatted_slice = []
    for i in xrange(len(slice.shape)):
        formatted_slice.append([j for j in xrange(_slice[i])])

    return tensor.__getitem__(formatted_slice)


def now_milliseconds():
    now = datetime.datetime.now()
    return (now.days * 24. * 60. * 60. + now.seconds) * 1000. + now.microseconds / 1000.


def send_json(conn, dict_to_transform):
    data = json.dumps(dict_to_transform)
    conn.send(HEADER_JSON)
    conn.send(len(data))
    conn.send(data)


def send_raw_numeric(conn, numeric):
    flat = numeric.flatten()
    data = struct.pack(flat)
    conn.send(HEADER_NUMERIC)
    conn.send(len(data))
    conn.send(data)


def we_are_not_the_server(meta, meta_rlock, orig):
    with meta["server"] as server:
        server_ip = copy.copy(server)
    
    return {
        "query":"special_error",
        "type":"we_are_the_server",
        "server":server_ip,
        "in_resp":orig
        }


def server_compatibility_check(meta, meta_rlock, query):
    with meta["server-queries"] as server_queries:
        test = query in server_queries

    return test    

def brecv(conn, size):
    # socket.MSG_WAITALL doesnt work on all platforms
    buff = conn.recv(size)
    print("buff is of size {current_size} of expected {expected_size}".format(current_size=len(buff), expected_size=size))
    while len(buff) < size:
        buff += conn.recv(size - len(buff))
        print("buff is of size {current_size} of expected {expected_size}".format(current_size=len(buff), expected_size=size))
    return buff

def receive_json(conn):
    bytes_to_receive = struct.unpack("i", brecv(conn, struct.calcsize("i")))[0]
    str_data = brecv(conn, bytes_to_receive)
    print("receive_json :: got string of size {len}, was expecting {bytes_to_receive}"\
        .format(len=len(str_data), bytes_to_receive=bytes_to_receive))

    raw = struct.unpack("%ds" % bytes_to_receive, str_data)[0]
    print("string received : %s" % raw)
    data = json.loads(raw)
    print(data)

    return data
