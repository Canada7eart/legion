from __future__ import absolute_import
"""
This is to allow the users to do something like

    from socialism import Server
    server = Server()

and

    from socialism import Client
    client = Client()

which are really by far the most important usecases. The client one, most importantly.

"""
import socialism.param_serv.Server
import socialism.Client

Server = socialism.param_serv.Server.Server
Client = Client.Client