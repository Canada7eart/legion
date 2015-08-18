from __future__ import print_function, division, absolute_import
__author__ = 'Jules Gagnon-Marchand'

from blocks.extensions import SimpleExtension
from socialism import Client
import time, os

class SocialistSync(SimpleExtension):
    # make sure to specify the argument "every_n_batches=T" when you instantiate this extension,
    # or something to that effect to determine how often we want to call it

    def __init__(self,
                 params,
                 alpha,
                 beta,
                 debug=False,
                 verbose=False,
                 **kwargs):

        super(SocialistSync, self).__init__(**kwargs)
        self.client = Client()
        self.debug = debug
        self.params = params
        self.alpha = alpha
        self.beta = beta
        self.verbose = verbose
        self.initialize_values(self.client, params, verbose)
        self.counter = 0

    def do(self, which_callback, *args):
        for name, val in self.params.iteritems():
            self.client.push_full(name, val.get_value(), self.alpha, self.beta)
            val.set_value(self.client.pull_full(name))

    @staticmethod
    def initialize_values(client, params, verbose):
        for name, val in params.iteritems():
            val.set_value(client.create_if_not_already_created(name, val.get_value()))