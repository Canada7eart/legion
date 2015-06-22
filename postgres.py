#!/usr/bin/env python2
from __future__ import print_function, with_statement, division, generators
import os, sys, re, threading, socket, time, random
import subprocess as sp
import psycopg2 as pg

def our_ip():
    return socket.gethostbyname(socket.gethostname())

def getTOD():
    return time.strftime("%H:%M:%S", time.gmtime())


DATABASE_URL = "opter.iro.umontreal.ca"
DATABASE_NAME = "gagnonmj_db"
# we don't know this one yet
DATABASE_PORT = 666

pgparams = {
        "database": "gagnonmj_db",
        "user":     "gagnonmj",
        "password": "a365c5e839",
        "host":     "opter.iro.umontreal.ca",
    }


if __name__ == "__main__":
    conn = pg.connect(**pgparams)
    cur = conn.cursor()
    cur.execute("INSERT INTO task (id) values (0)")
    cur.execute("INSERT INTO job (id, task) values (0, 0)")
    cur.execute("INSERT INTO NODE (id, ip) values (0, \"%s\")", "127.0.0.1")
    cur.execute(
        "INSERT INTO process (id, pid, node, state, \
            node, port, job_id) values (%d, %d, %s, %s, %s, %s, %s)", int(random.random() * 1000), os.getpid(), 0, 0, 0, 0, 0)
    conn.commit()
    cur.close()
    conn.close()
    print("done.")