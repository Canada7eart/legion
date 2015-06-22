#!/usr/bin/env python2
from __future__ import print_function, with_statement, division, generators
import os, sys, re, threading, socket, time
import subprocess as sp
import psycopg2 as pg


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
    print(conn)
