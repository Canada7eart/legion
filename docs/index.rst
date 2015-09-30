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

.. tips::
   Adaptating your Blocks (or Theano) programs to use Legion is relatively easy,
   but getting a performance gain with Legion is not trivial.
   One rule of thumb seems to be that, if you can run through your whole dataset
   relatively quickly (let's say less than 30 seconds), then you probably will
   not get anything out of using Legion. Stay with regular SGD.

.. _Blocks: https://github.com/mila-udem/blocks


Overview
--------

have a sketch here

Quick example
--------

detail some steps and bash commands



Specific examples explained
--------
.. toctree::
   :maxdepth: 1

   example_blocks_tutorial.rst
   ../examples/blocks_tutorial/tuto0.py


|

Indices and tables
==================
* :ref:`genindex`
* :ref:`modindex`