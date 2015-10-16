Explanation about the Blocks extensions
=================================


Parameter synchronization
--------

The preferred method to handle parameter synchronization
is to use the solution provided in Blocks, which comes through
either the ``SharedParamsAutoSync`` or ``SharedParamsRateLimited``
extension. The second is just a more complete form of the first.

>>> from legion.blocks_extensions import SharedParamsAutoSync, SharedParamsRateLimited

The parameters on the server are updated according to the rules
in the :doc:`description of the python API<python_api>`, involving
the two constants ``alpha`` and ``beta``. Essentially, we update
each parameter with the rule

>>> value = alpha * value + beta * new_value

The extension requires those parameters ``alpha`` and ``beta``.
Usually, we just have that ``beta=1.0-alpha``.

>>> SharedParamsAutoSync(params_to_sync, alpha=0.5, beta=0.5)




                                 SharedParamsRateLimited(params=params_to_sync, every_n_batches=1, alpha=0.5, beta=0.5, maximum_rate=0.25),




Timestamps
--------

.. tip:: There are two extensions dealing with timing : ``Timestamp`` and ``StopAfterTimeElapsed``.

>>> from legion.blocks_extensions import Timestamp, StopAfterTimeElapsed

The ``legion.blocks_extensions.Timestamp`` extension is
a way to adding logging to the training so that we can more
easily reconcile the work done by different workers.

In the context of ASGD, we can have different workers starting
at different times (based on the cluster scheduling),
and the only way to plot the train/valid loss in a coherent way
is to have timestamps on the workers.

The ``legion.blocks_extensions.Timestamp`` extension requires no
special argument besides the usual ``every_n_batches``
to specify when it should be run.

>>> Timestamp(every_n_batches=10)

Look at the 'datestamp' and 'timestamp' fields in your logs from
Blocks' main loop. The data saved takes the following form :

>>> current_row['datestamp'] = time.strftime("%Y-%m-%d %H:%M")
>>> current_row['timestamp'] = time.time()




The ``legion.blocks_extensions.StopAfterTimeElapsed`` extension is
one of two ways to specify when a worker should stop training.
One of the ways is to use a "walltime" argument when launching legion,
but that's a limit that has to do with the cluster and it does not
terminate the jobs gracefully. The preferred way is to include
the ``StopAfterTimeElapsed`` extension in your usual list, and
specify the total duration (in seconds) that the training should last.
We need to specify how often the extension runs to make sure
that we check if training has gone over the time limit.

>>> StopAfterTimeElapsed(every_n_batches=1, total_duration=maximal_total_duration),
