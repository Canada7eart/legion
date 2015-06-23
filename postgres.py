#!/usr/bin/env python2
from __future__ import print_function, with_statement, division, generators
import os, sys, re, threading, socket, time, random
import subprocess as sp
import psycopg2 as pg

def our_ip():
    return socket.gethostbyname(socket.gethostname())

def getTOD():
    return time.strftime("%H:%M:%S", time.gmtime())

pgparams = {
        "database": "gagnonmj_db",
        "user":     "gagnonmj",
        "password": "a365c5e839",
        "host":     "opter.iro.umontreal.ca",
    }


def update_proc_state(proc_id, new_state):
    conn = pg.connect(**pgparams)
    cur = conn.cursor()
    cur.execute(
        "UPDATE state VALUES(%s) FROM process WHERE proc_id = %s", (new_state, proc_id, ))
    conn.commit()
    cur.close()
    conn.close()

def save_proc_entry(job_id, node, port):
    conn = pg.connect(**pgparams)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO process (id, pid, state, node, port, job_id) \
                      values (%s,  %s,    %s,   %s,   %s,     %s)", \
                      (str(node) + str(os.getpid()), str(os.getpid()), "ONLINE", node, port, job_id, ))
    conn.commit()
    cur.close()
    conn.close()

def get_proc_info(proc_id):

    conn = pg.connect(**pgparams)
    cur = conn.cursor()
    basic_stuff = cur.execute("SELECT pid, state, node, port from process where id=%s", (proc_id, ))
    ip = cur.execute("SELECT ip from node where id = %s", (basic_stuff["node"], ))
    cur.close()
    conn.close()

    return {"process": basic_stuff, "node": {"ip": ip}}
