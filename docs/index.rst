Welcome to Legion' documentation!
=================================
Legion is a machine learning and deep learning distributed training solution.

It is currently at a late prototype stage and it is intended for use
a the University of Montreal on clusters such as Helios.

It contains an implementation of Asynchronous Stochastic Gradient Descent (ASGD) with:

* parameter server in python
* Blocks_ extensions to synchronize the parameters on individual workers with the parameter server
* script to launch everything on the Helios cluster
* examples of scripts adapted to be used with Legion

For more information about the Helios cluster (from Calcul Quebec), see:

* http://www.calculquebec.ca/en/resources/compute-servers/helios
* https://wiki.calculquebec.ca/w/Helios/en

.. warning::
   Legion is not a way to use multiple GPUs in one Theano process.

.. warning::
   Legion is not a good strategy to explore a large collection of hyper-parameters;
   it is meant to speed up ONE experiment being trained.

.. tip::
   Adaptating your Blocks (or Theano) programs to use Legion is relatively easy,
   but getting a performance gain with Legion is not trivial.
   One rule of thumb seems to be that, if you can run through your whole dataset
   relatively quickly (let's say less than 30 seconds), then you probably will
   not get anything out of using Legion. Stay with regular SGD.

.. _Blocks: https://github.com/mila-udem/blocks


Overview
--------

.. image:: /_static/legion_overview_usage_diagram.svg
   :width: 60%


Quickstart
--------

Clone the library and install the python module.

.. code-block:: bash
   $ git clone git@github.com:JulesGM/legion.git legion
   $ cd legion
   $ python setup.py develop --user

Modify your Blocks experiment to add the special legion modules that feature automatic parameter synching.
See particular examples for how to build a dictionary of theano shared variables representing the model parameters.
This is facilitated by the fact that Blocks gives access to the computational graph.

>>> from legion.blocks_extensions import SharedParamsAutoSync, SharedParamsRateLimited
>>> from legion.blocks_extensions import Timestamp, StopAfterTimeElapsed
>>> # build the dictionary of parameters
>>> params_to_sync = ...
>>> # instantiate Blocks extension to be used in MainLoop
>>> special_extension = SharedParamsRateLimited(params=params_to_sync, every_n_batches=1, alpha=0.5, beta=0.5, maximum_rate=0.25)

Debug the thing locally and then move over to the Helios cluster, where everything has to be set up again in the usual way.

.. code-block:: bash
    $ ssh helios.calculquebec.ca
    $ screen -S my_experiment
    $ cd pathto/legion
    $ bin/legion pathto/run_blocks_experiment.py --allocation="jvb-000-ag" --instances=4 --walltime=3:00:00

The execution of ``bin/legion`` takes over this screen and will only end when you hit ``ctrl-c``.
This means that the parameter server is running on the entry node ``helios1`` of the Helios cluster.
It consumes reasonably little computation power and we have been given permission to run this
on the entry node by the administrators of the Helios cluster (because it's a derogation to the usual rules
that say that the entry node is not meant to run jobs).


Within another screen, you can check on the queued jobs by using ``showq``.




Specific examples explained
--------
.. toctree::
   :maxdepth: 1

   example_blocks_tutorial.rst
   ../examples/blocks_tutorial/tuto0.py
