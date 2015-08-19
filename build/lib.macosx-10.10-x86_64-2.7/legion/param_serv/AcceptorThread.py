#!/usr/bin/env python2
from __future__ import print_function, with_statement, division, generators
import socket, sys, os, threading
from traceback import format_exc

from legion.param_serv.param_utils import *
from legion.param_serv.ReceptionThread import ReceptionThread

class AcceptorThread(threading.Thread):
    """
    This is the server's acceptor thread. The server has one of these.
    Constantly loops to create "ReceptionThread"s when a connection to a client is accepted.
    """
    def __init__(self, instances, meta, meta_rlock, db, db_rlock):
        super(self.__class__, self).__init__()
        self.meta =                 meta
        self.meta_rlock =           meta_rlock
        self.db =                   db
        self.db_rlock =             db_rlock
        self.sock =                 None
        self.instances =            instances
        self.instances_counter =    0
        self.reception_threads =    []

    def join_reception_threads(self):
        for reception_thread in self.reception_threads:
            reception_thread.join()

    def bind(self):
        """
        This is where the port is bound.
        We leave the decision of which port to bind to the OS, by binding on port 0,
        which asks the OS to decide which port we bind to.

        :return: The port that is bound to the server
        """
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

            self.sock.bind(('', 0))
            #self.sock.getsockname()[1]
            self.sock.listen(100)

        except socket.error, s_err:
            if s_err.errno == 48:
                pwh(format_exc())
                return None
            else:
                raise s_err

        return self.sock.getsockname()[1]

    def run(self):
        """
        This is the server's acceptor thread. The server has one of these.
        Constantly loops to create "ReceptionThread"s when a connection to a client is accepted.

        :return: Nothing. Should never actually return.
        """
        try:
            while True:
                pwh("Waiting for a connection")
                conn, addr = self.sock.accept()
                pwh("Established new connection.")
                new_thread = ReceptionThread(
                    conn,
                    self.meta,
                    self.meta_rlock,
                    self.db,
                    self.db_rlock)

                new_thread.setDaemon(True)
                new_thread.start()
                self.instances_counter += 1
                if self.instances_counter >= self.instances:
                    print("The acceptor has received all the threads it expected.")
                    break


        finally:
            if self.sock:
                self.sock.close()


