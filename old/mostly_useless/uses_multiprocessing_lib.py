from __future__ import print_function, with_statement, division, generators
# Echo server program
import socket, json, struct
import threading
import subprocess as sp
import sys, os, re, argparse, copy, time, datetime
import curses
import multiprocessing

def kill_time():
    while True:
        time.sleep(10)

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
    server = multiprocessing.Process(target=kill_time)
    server.daemon = False
    server.start()
    print("waiting for server")
    
    client = multiprocessing.Process(target=kill_time)
    client.daemon = False
    client.start()
    print("waiting for client")
    
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
                client.terminate()
            
            if ch == ord("s"):
                server.terminate()

            if client.is_alive():
                state_client = "alive"
            else :
                state_client = "dead"
            
            if server.is_alive():
                state_server = "alive"
            else :
                state_server = "dead"
            
            
            win.border(0)
            win.addstr(2, 3, "Boss   (%d) - alive (obviously)" % (os.getpid()))
            win.addstr(4, 3, "Server (%d) - %s" % (server.pid, state_server))
            win.addstr(6, 3, "Client (%d) - %s" % (client.pid, state_client))
            win.addstr(9, 3, "Press 'b' kill Boss, 's' to kill Server and 'c' to kill Client.")
            win.refresh()

if __name__ == '__main__': 
    main()