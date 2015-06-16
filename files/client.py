#!/usr/bin/env python2

from __future__ import print_function, with_statement, division, generators
import os, sys, re, threading, socket, argparse, time, traceback

def our_ip():
    return socket.gethostbyname(socket.gethostname())

def main():
    PBS_NODENUM = os.environ.get("PBS_NODENUM", "[there was no PBS_NODENUM]")

    parser = argparse.ArgumentParser()
    
    parser.add_argument('--path', nargs=1, type=str)
    args = parser.parse_args()
    assert args.path, "path was None"
    path = args.path[0]
    assert path != "", "base_file_path was an empty string"

    print("Node num #%s: base_file_path: %s" % (PBS_NODENUM, path,))
    
    server = None
    we_are_the_server = None

    while True:
        try:
            if os.path.exists(path):
                with open(path, "r") as f:
                    print("Node num #%s: We successfully opened the file in R mode" % (PBS_NODENUM,))
                    server = f.next()
                    we_are_the_server = False
                    break
            else:
                with open(path, "w") as f:
                    print("Node num #%s: We successfully opened the file in W mode" % (PBS_NODENUM,))
                    f.write(our_ip())
                    we_are_the_server = True
                    break
                    
        except Exception, err:
            print(err)
            traceback.print_exc(file=sys.stdout)
            time.sleep(1)
    
    if we_are_the_server:
        print("Node num #%s: We are the server. Our ip is %s." % (PBS_NODENUM, our_ip(),))
    
    else:
        print("Node num #%s: We aren't the server. The server's ip is %s." % (PBS_NODENUM, server))
    
    with open(os.path.join(os.getcwd(), PBS_NODENUM + "_text.txt"), "w") as of:
        of.write("yooo")
if __name__ == '__main__': 
    main()
