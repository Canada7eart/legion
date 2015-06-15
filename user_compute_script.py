""" Extremely simple launch script. Should be improved. """
#!/usr/bin/env python2

from __future__ import print_function, with_statement, division, generators
import os, sys, re, threading, socket, argparse
import subprocess as sp

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--launcher-ip', nargs=1, type=str)
    parser.add_argument('--launcher-port', nargs=1, type=str)
    args = parser.parse_args()
    print("Trying to connect to %s:%s" % (str(args.launcher_ip[0]), str(args.launcher_port[0])))

    socket.create_connection((args.launcher_ip[0], args.launcher_port[0]))
    print("Logic would tell us the connection worked.")
if __name__ == '__main__':
    main()
