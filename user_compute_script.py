""" Extremely simple launch script. Should be improved. """
#!/usr/bin/env python2

from __future__ import print_function, with_statement, division, generators
import os, sys, re, threading, socket, argparse, time
import subprocess as sp

def getTOD():
    return time.strftime("%H:%M:%S", time.gmtime())


def entete():
    return "PBS_NODENUM#%s - %s" % (getTOD(), s.environ["PBS_NODENUM"],)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--launcher-ip', nargs=1, type=str)
    parser.add_argument('--launcher-port', nargs=1, type=str)
    args = parser.parse_args()


    print("%s: Trying to connect to %s:%s" % (entete(), str(args.launcher_ip[0]), str(args.launcher_port[0])))

    socket.create_connection((args.launcher_ip[0], args.launcher_port[0]))

    print("%s: Logic would tell us the connection worked." % (entete()))

if __name__ == '__main__':
    main()
