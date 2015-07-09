from __future__ import print_function, with_statement, division, generators
import socket
import json
import struct
import threading
import os
import time
import datetime
from traceback import print_exc

from headers import *


def our_ip():
    return socket.gethostbyname(socket.gethostname())

def insert_tabs(text):
    return "\t" + text.replace("\n","\n\t")

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

def send_numeric_from_bytes(conn, bytes):
    conn.sendall(struct.pack("ii%ds" % len(bytes), HEADER_NUMERIC, len(bytes), bytes))
    # conn.sendall(struct.pack("ii", HEADER_NUMERIC, len(bytes)) + bytes)

def send_json(conn, dict_to_transform):
    data = json.dumps(dict_to_transform)
    conn.sendall(struct.pack("ii%ds" % len(data),  HEADER_JSON,    len(data),  data))

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
    return buff

def receive_json(conn):
    bytes_to_receive = struct.unpack("i", brecv(conn, struct.calcsize("i")))[0]
    str_data = brecv(conn, bytes_to_receive)
    raw = struct.unpack("%ds" % bytes_to_receive, str_data)[0]
    try:
        data = json.loads(raw)
        
    except ValueError, err:
        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        print(">>>>> json conversion failed - Raw: %s" % raw)
        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        print_exc()
        exit(-1)

    return data
