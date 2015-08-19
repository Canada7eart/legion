from __future__ import absolute_import

"""
This is to allow the users to do something like

    from legion import Server
    server = Server()

and

    from legion import Client
    client = Client()

which are really by far the most important usecases. The client one, most importantly.

"""
import legion.param_serv.Server
Server = legion.param_serv.Server.Server

from .Client import Client

