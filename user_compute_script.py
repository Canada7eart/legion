#!/usr/bin/env python2
from __future__ import print_function, with_statement, division, generators
""" Extremely simple launch script. Should be improved. """


PORT = 6000
import os, sys, re, threading, socket, argparse, time
import subprocess as sp
import pg8000
import database_interface as dbi

def getTOD():
    return time.strftime("%H:%M:%S", time.gmtime())

def header():
    return "PBS_NODENUM#%s - %s" % (getTOD(), os.environ["PBS_NODENUM"], )

# print_with_header
def pwh(text):
    print("{header}: {text}".format(
        header=header(), 
        text=text))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sql_server_ip',   nargs=1, type=str)
    parser.add_argument('--sql_server_port', nargs=1, type=str)
    parser.add_argument('--job_name',          nargs=1, type=str)
    parser.add_argument('--debug',           action="store_true")

    args = parser.parse_args()

    pwh("Saving ip to database.")
    db = dbi.Db(pg8000, args.job_name[0]) 

    node_num = os.environ["PBS_NODENUM"] if args.debug else "0"

    db.save_proc_entry(node_num, PORT)
    pwh("Done.")

if __name__ == '__main__':
    main()
