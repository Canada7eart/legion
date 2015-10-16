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

>>> SharedParamsAutoSync(params_to_sync, alpha=0.5, beta=0.5, every_n_batches=20)

The ``params_to_sync`` parameter is a dictionary of theano shared variables
whose keys are unique names. Be careful about using the default names
given to theano variables because they might not be unique.

The values in that dictionary are going to be modified with their
``set_value`` and ``get_value`` methods.

Be sure that all the workers are using the same names to refer
to the same quantities. Calling something "weights" is fine
if only one parameter in the whole model is going to have that
name. When listing the theano variables as "weights_00", "weight_01"
and so on, make sure that you list the variables in the same
order on every worker. Otherwise, you will get nonsensical updates.

Refer to the :doc:`description of the python API<python_api>` for
more information about what to do and what to avoid.

Be careful to avoid ``every_n_batches=1`` because that would
create a bottleneck where the time spent in synchronization
is much more than the time spent running data through your model.




The slightly more elaborate extension is ``SharedParamsRateLimited``.
In practice, you will use this one 95% of the time. It is a subclass
of the extension ``SharedParamsAutoSync`` described above, but it
also features a mechanism to limit the amount of time spent synchronizing
parameters with the server.

>>> SharedParamsRateLimited(params=params_to_sync, every_n_batches=1, alpha=0.5, beta=0.5, maximum_rate=0.25)

The extra argument here is the ``maximum_rate=0.25``,
which specifies that the extension should not spend
more than 25% of the total running time on itself.
Using ``every_n_batches=1`` is a good idea here.
This means that, whenever the extension is run,
it takes into consideration how much time it took on
the previous synchronization, and how much time has
elapsed since then, and it makes the decision based on that.
This counts the ``set_value`` and ``get_value`` as part
of the synchronization cost.

It will try to get as close to 25% without exceeding it.
It has an little decay mechanism inside to be more robust
to sudden delays that would lead to a bad estimate of
the synchronization costs.

That ``maximum_rate`` should be based loosely on
the number of workers in that experiment. There is no danger
of oversaturating the parameter server because this
extension will automatically compensate for this.
When synchronization operations take twice as long,
it will synchronize twice as rarely to balance out.

As a rule of thumb, ``maximum_rate`` should probably
be below 0.5, and a more reasonable rate would probably
be around 0.5/nbr_of_workers. But that's not justified
by any theory.




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
