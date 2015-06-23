#!/usr/bin/env python2

from __future__ import print_function, with_statement, division, generators
# Echo server program
import socket, json, struct
import threading
import subprocess as sp
import sys, os, re, argparse, copy, time, datetime
import curses
import signal, psutil


def get_children():
    p = psutil.Process(os.getpid())
    children = p.children(recursive=False) 
    
    return children

def kill_time():
    while True:
        time.sleep(10)

# TODO:
def find_out_our_ip():
    assert False, "TODO"
    
# TODO:
def find_out_our_node():
    assert False, "TODO"
    
# TODO:
def find_ips_and_ports_of_other_nodes():
    assert False, "TODO"
    
class CursesScreen(object):
    def __enter__(self):
        self.stdscr = curses.initscr()
        curses.cbreak()
        curses.noecho()
        self.stdscr.keypad(1)
        SCREEN_HEIGHT, SCREEN_WIDTH = self.stdscr.getmaxyx()
        return self.stdscr

    def __exit__(self, a, b, c):
        curses.nocbreak()
        self.stdscr.keypad(0)
        curses.echo()
        curses.endwin()


def main():
    we_are_the_server = "--server" in sys.argv
    meta = {
        "we_are_the_server": copy.copy(we_are_the_server),
    }
    meta_lock = RLock()
    db = {}
    db_lock = RLock()

    if we_are_the_server:         
        if server == 0:
            kill_time()
            exit(0)
        server_pid = get_children()[0]

    client = os.fork()
    
    if client == 0:
        kill_time()
        exit(0)

    client_pid = [x for x in get_children() if x.pid != server_pid.pid][0]

    with CursesScreen() as win:
        curses.echo()
        win.timeout(500)

        while True:

            state_server = None
            state_client = None

            ch = win.getch()
            
            win.erase()
            if ch != -1:
                win.addstr(11, 3, "%s" % chr(ch))
        
            if ch == ord("b") or ch == ord("q"):
                exit()
            
            if ch == ord("c"):
                client_pid.terminate()
            
            if ch == ord("s"):
                server_pid.terminate()

            win.border(0)
            win.addstr(2, 3, "Boss   (%d) - alive (obviously)" % (os.getpid()))
            win.addstr(4, 3, "Server (%d) - %s" % (server_pid.pid, server_pid.is_running() and not server_pid.status() == psutil.STATUS_ZOMBIE))
            win.addstr(6, 3, "Client (%d) - %s" % (client_pid.pid, client_pid.is_running() and not client_pid.status() == psutil.STATUS_ZOMBIE))
            win.addstr(9, 3, "Press 'b' kill Boss, 's' to kill Server and 'c' to kill Client.")
            win.refresh()

if __name__ == '__main__': 
    main()
