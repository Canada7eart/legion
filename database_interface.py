#!/usr/bin/env python2
from __future__ import print_function, with_statement, division, generators
import os, sys, re, threading, socket, time, random, struct, json
import subprocess as sp

def our_ip():
    return socket.gethostbyname(socket.gethostname())

def getTOD():
    return time.strftime("%H:%M:%S", time.gmtime())

pgparams = {
        "database": "gagnonmj_db",
        "user":     "gagnonmj",
        "password": "a365c5e839",
        "host":     "opter.iro.umontreal.ca",
    }

class Db(object):
    def __init__(self, db, job_name, conn_params = pgparams):
        
        self.db = db
        self.conn = self.db.connect(**pgparams)
        self.job_name = job_name

    def update_proc_state(self, proc_id, new_state):
        """ Can fail. """

        cur = self.conn.cursor()
        cur.execute(
            "UPDATE state VALUES (%s) FROM process WHERE proc_id = %s", 
            (new_state, proc_id, )
            )

        self.conn.commit()
        cur.close()


    def save_proc_entry(self, node, port):
        """ Should not fail. If it does, it's a bug; we know we're alive. """
        
        cur = self.conn.cursor()

        print("job_name: {job_name}".format(job_name=self.job_name))
        sys.stdout.flush()

        cur.execute(  
            "INSERT INTO process (id, pid, state, node, port, job_name) \
                          values (%s,  %s,    %s,   %s,   %s,     %s)", 
            ("{node}::{pid}".format(node=node, pid=os.getpid()), 
                str(os.getpid()), "ONLINE", node, port, self.job_name, )
            )

        self.conn.commit()
        cur.close()

    def get_proc_info(self, proc_id):
        """ Can fail. """

        cur = self.conn.cursor()
        basic_stuff = cur.execute("SELECT pid, state, node, port from process where id=%s", (proc_id, ))
        ip = cur.execute("SELECT ip from node where id = %s", (basic_stuff["node"], ))
        cur.close()

        if basic_stuff:
            return {
                "process": basic_stuff, 
                "node": {
                    "ip": ip
                    }
                }

        else :
            return None

    def check_livess_of_other_nodes(self):

        cur = self.conn.cursor()
        ips_and_ports = cur.execute("SELECT pid, port, is_server FROM PROCESS WHERE job_name = %s and state = 'ACTIVE', \
            inner join select ip from node where node.id = process.node", (self.job_name,))

        curr.commit()
        curr.close()
        
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

    def start_replacing_server(self):
        # we are initiating the server replacement protocol.
        # it mights gave started elsewhere

        cur = self.conn.cursor()
        ips_and_ports = cur.execute("SELECT pid, port FROM PROCESS WHERE job_name = %s and state = 'ACTIVE', \
            inner join select ip from node where node.id = process.node", (self.job_name,))

        curr.commit()
        curr.close()

        conns = {}

        for ip, port in ips_and_ports:
            try:
                conns[(ip, port)] = socket.create_connection(address=ip, timeout=5, port=port)
                conns[(ip, port)].send(struct.pact(JSON_HEADER,"i"))
                json_text = json.dump({
                    "query": "select_new_server",
                    "ips": ips_and_ports
                    })

                conns[(ip, port)].send(struct.pact(len(json_text), "i"))
                conns[(ip, port)].send(struct.pact(json_text, "s"))

                """ 
                -> disable the starting of other "start_replacing_server" initiative
                -> answer to other "start_replacing_server" initiatives by a message saying you're already engaged
                -> 
                """

            except:
                assert False, "TODO"











