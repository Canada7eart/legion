from __future__ import print_function, division, absolute_import
__author__ = 'Jules Gagnon-Marchand'

from blocks.extensions import SimpleExtension
from legion import Client
import time, os

class SharedParamsAutoSync(SimpleExtension):

    # Make sure to specify the argument "every_n_batches=T" when you instantiate this extension,
    # or something to that effect to determine how often we want to call it.
    #
    # If the parameters are already set up on the server,
    # they will get read (and not reinitialized).
    # If the parameters are not configured on the server,
    # they will be created and take on the same values
    # as when this extension is called for the first time.

    def __init__(self,
                 params,
                 alpha,
                 beta,
                 client=None
                 debug=False,
                 verbose=False,
                 **kwargs):

        super(SharedParamsAutoSync, self).__init__(**kwargs)
        assert type(params) == list
        if client is None:
            self.client = Client()
        self.debug = debug
        self.params = params
        self.alpha = alpha
        self.beta = beta
        self.verbose = verbose
        self.initialize_values(self.client, params, verbose)

    def do(self, which_callback, *args):
        if self.should_we_sync_now():
            self.presync_callback()
            # perform the actual work here
            for name, val in self.params.iteritems():
                self.client.push_full(name, val.get_value(), self.alpha, self.beta)
                val.set_value(self.client.pull_full(name))
            # done
            self.postsync_callback()


    @staticmethod
    def initialize_values(client, params, verbose):
        for name, val in params.iteritems():
            val.set_value(client.create_if_not_already_created(name, val.get_value()))


    # These next functions are to support a bit of polymorphism
    # for other subclasses that will instrument this class a bit more.

    def presync_callback():
        pass

    def postsync_callback():
        pass

    def should_we_sync_now():
        return True





