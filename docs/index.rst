Welcome to Legion' documentation!
=================================
Legion is a machine learning and deep learning distributed training solution.

It is currently at a late prototype stage and it is intended for use
a the University of Montreal on clusters such as Helios.

It contains an implementation of Asynchronous Stochastic Gradient Descent (ASGD) with 
* parameter server in python
* Blocks_ extensions to synchronize the parameters on individual workers with the parameter server
* script to launch everything on the Helios cluster
* examples of scripts adapted to be used with Legion

For more information about Helios, check out

http://www.calculquebec.ca/en/resources/compute-servers/helios
https://wiki.calculquebec.ca/w/Helios/en

.. warning::
   Legion is not a way to use multiple GPUs in one Theano process.
   Legion is not a good strategy to explore a large collection of hyper-parameters.

.. tips::
   Adaptating your Blocks (or Theano) programs to use Legion is relatively easy,
   but getting a performance gain with Legion is not trivial.
   One rule of thumb seems to be that, if you can run through your whole dataset
   relatively quickly (let's say less than 30 seconds), then you probably will
   not get anything out of using Legion. Stay with regular SGD.



Want to get try it out? Start by :doc:`installing <setup>` Blocks and having a
look at the :ref:`quickstart <quickstart>` further down this page. Once you're
hooked, try your hand at the :ref:`tutorials <tutorials>`.

Blocks is developed in parallel with Fuel_, a dataset processing framework.

.. _Blocks: https://github.com/mila-udem/blocks

|

Indices and tables
==================
* :ref:`genindex`
* :ref:`modindex`