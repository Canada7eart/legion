Description of the python API to the parameter server
=================================

The words "client" and "workers" are used almost interchangeably here.
They refer to the fact that scheduled jobs on the cluster are designed
to perform work, which is then synchronized with the parameter server.
The word "client" refers to the fact that this is a connection going
through a TCP/IP socket.

In the context of the python API, we do not
make any assumption about the clients being workers,
but simply want to talk about the fact that a number
of clients are all synchronizing a certain number
of parameters with a server.


Where are the client workers supposed to be configured to talk to the parameter server ?
--------

When ``bin/legion`` is called from the command-line, it queues the
workers to be run on Helios, and then it turns into the parameter server.
This lasts until the user hits ``CTRL-C``.

It sets up environment variables (such as "legion_server_ip" and "legion_server_port")
which are going to get picked up by the workers to be able
to connect to the server.

This means that individual clients do not have to know
anything about the parameter server. They only need to get
a copy of ``myclient = legion.Client()`` and then can do
everything from that.

.. tip::
    You do not need to specify anything about the parameter server's IP or port
    while on the client side.


Creating a client
--------

Here is a minimalist example of how to create a client
to communicate with the parameter server.

We want to synchronize a parameter called "my_matrix".

>>> import numpy as np
>>> from legion import Client
>>>
>>> client = Client()
>>> alpha = 0.5
>>> beta = 0.5
>>>
>>> A = np.random.rand(5,5)
>>> # Notice the pattern of respecting the possibility
>>> # that this parameter already exists on the server
>>> # and that you should start from that existing value.
>>> client.create_if_not_already_created("my_matrix", A)
>>> A = client.pull_full("my_matrix")
>>>
>>> for i in range(20):
>>>     A = client.pull_full("my_matrix")
>>>     ## do some work here with `A` ##
>>>     client.push_full("my_matrix", A, alpha, beta)
>>>

Note that we call ``create_if_not_already_created`` at first,
because only one of the clients will actually get to
initialize that parameter on the server. In all the other
cases, the clients will communicate with the server and
the server will drop that request because there already
exists a parameter with that name.

This means that we then have to request the current value
of that parameter from the server. Think about the situation
where a client shows up one hour late. It tells the server :
"Hey, if I'm the one who first told you about this variable 'my_matrix',
then use my value. Otherwise, please tell me what you currently have
and I'll start from there."


Update rules
--------

As hinted briefly in the :doc:`description of the Blocks extensions <blocks_extensions>`,
the updates take two arguments ``alpha`` and ``beta``.

The updates sent with ``client.push_full(name, new_value, alpha, beta)``
are sent to the server, who performs the following update locally :

>>> value = alpha * value + beta * new_value

This way of phrasing things is in the spirit of the BLAS operations
that have that kind of prototype.

Note that, if you use the updates to communicate new values,
you should generally have that ``beta=1.0-alpha``.
This is how the Blocks extensions provided work.

If you want to use the parameter server to push "differences",
you are free to use ``alpha`` and ``beta`` in a way that makes sense
for this. For example, you might use ``alpha=1.0`` and ``beta=0.1``
so that the end result of ``client.push_full(name, diff_value, 1.0, 0.1)``
on the server would be mathematically equivalent to :

>>> value += beta * diff_value


