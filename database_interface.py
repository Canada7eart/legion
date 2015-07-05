#!/usr/bin/env python2
from __future__ import print_function, with_statement, division, generators
import os, sys, re, threading, socket, time, random, struct, json
import subprocess as sp
import pg8000

from param_serv.param_utils import *

pgparams = {
        "database": "gagnonmj_db",
        "user":     "gagnonmj",
        "password": "a365c5e839",
        "host":     "opter.iro.umontreal.ca",
    }

class Db(object):
    def __init__(self, db, task_name, job_name, conn_params):
        
        self.db = db
        self.conn = self.db.connect(**conn_params)
        self.job_name = job_name
        self.task_name = task_name

    def update_proc_state(self, proc_id, new_state):
        """ Can fail. """

        cur = self.conn.cursor()
        cur.execute(
            "UPDATE state VALUES (%s) FROM process WHERE proc_id = %s", 
            (new_state, proc_id, )
            )

        self.conn.commit()
        cur.close()


    def save_proc_entry(self, port):
        """ Should not fail. If it does, it's a bug; we know we're alive. """
        
        cur = self.conn.cursor()

        print("job_name: {job_name}".format(job_name=self.job_name))
        sys.stdout.flush()

        cur.execute(  
            "INSERT INTO process (id, pid, state, ip, port, job_name) \
                          values (%s,  %s,    %s,   %s,   %s,     %s)", 
            ("{ip}::{pid}".format(ip=our_ip(), pid=os.getpid()), 
                str(os.getpid()), "ONLINE", our_ip(), port, self.job_name, )
            )
        
        cur.close()
        self.conn.commit()
        
    def get_proc_info(self, proc_id):
        """ Can fail. """

        cur = self.conn.cursor()
        basic_stuff = cur.execute("SELECT pid, state, node, port from process where id=%s", (proc_id, ))
        ip = cur.execute("SELECT ip from node where id = %s", (basic_stuff["node"], ))
        cur.close()
        self.conn.commit()

        if basic_stuff:
            return {
                "process": basic_stuff, 
                "node": {
                    "ip": ip
                    }
                }

        else :
            return None
    """
    def check_liveness_of_other_nodes(self):

        cur = self.conn.cursor()
        ips_and_ports = cur.execute("SELECT pid, port, is_server FROM PROCESS WHERE job_name = %s and state = 'ACTIVE', \
            inner join select ip from node where node.id = process.node", (self.job_name,))

        cur.commit()
        cur.close()
        
        print(tips_and_portsest)

        for pid, ip, port, is_server in ips_and_ports:
            try:
                conn = socket.create_connection(address=ip, timeout=5, port=port)

            except Exception, err:
                if not is_server:
                    # this can fail
                    self.update_proc_state(pid, "POTENTIALLY_DEAD")

                else:
                    self.start_replacing_server()
            else:
                conn.close()
    """

    def get_server_ip_and_port(self):
        cur = self.conn.cursor()
        cur.execute("SELECT server_ip, server_port FROM task WHERE name = %s", (self.task_name, ))
        ip, port = cur.fetchone()
        self.conn.commit()
        cur.close()
        return ip, port            


if __name__ == '__main__':
    db = Db(pg8000, "random_task_name", "0")
    text = db.get_server_ip()
    print(text)



