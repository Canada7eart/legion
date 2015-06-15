#!/usr/bin/env python2

from __future__ import print_function, with_statement, division, generators
# Echo server program
import socket, json, struct
import threading
import subprocess as sp
import sys, os, re, argparse, copy, time, datetime
import curses


class CursesScreen(object):
    def __enter__(self):
        self.stdscr = curses.initscr()
        curses.cbreak()
        curses.noecho()
        self.stdscr.keypad(1)
        SCREEN_HEIGHT, SCREEN_WIDTH = self.stdscr.getmaxyx()
        return self.stdscr

    def __exit__(self):
        curses.nocbreak()
        self.stdscr.keypad(0)
        curses.echo()
        curses.endwin()


if __name__ == '__main__':
    with CursesScreen() as win:
        while True:
            win.erase()
            win.border(0)
            proc = sp.Popen("qstat", stdout=sp.PIPE, stderr=sp.PIPE)
            text = proc.communicate()
            win.addstr(3, 3, text)
            time.sleep(1)



