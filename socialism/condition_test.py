from __future__ import with_statement
__author__ = 'jules'
import copy

import threading, sys, time
cond = threading.Condition()
still_some = 0

s_is_w = False
count = 0

read_event = threading.Event()
read_event.set()

write_event = threading.Event()


count_m = threading.RLock()

stdout_m = threading.RLock()



def lol(y):
    global cond
    global still_some
    global s_is_w
    global count
    global read_event
    global write_event
    global stdout_m

    serv = y == 3

    if not serv:
        with count_m:
            count += 1

        read_event.wait()

    if serv:
        write_event.wait()
        with stdout_m:
            print(">>>>>> doing server things")
        time.sleep(2)
        with stdout_m:
            print("<<<<<< done doing server things")
        read_event.set()
        return

    if not serv:
        with stdout_m:
            print("%d doing client things" % y)
        time.sleep(0.2)
        with stdout_m:
            print("%d done doing client things" % y)

        with count_m:
            count -= 1
            with stdout_m:
                print("%d count is %d" % (count, y))

            read_event.clear()
            if count == 0:
                write_event.set()
            else:
                read_event.set()

        return

threads = [threading.Thread(target=lol, args=(x,)) for x in xrange(20)]
for th in threads:
    th.start()
    time.sleep(0.1)
