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
                 client=None,
                 debug=False,
                 verbose=False,
                 **kwargs):

        super(SharedParamsAutoSync, self).__init__(**kwargs)
        assert type(params) == dict
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

    def presync_callback(self):
        pass

    def postsync_callback(self):
        pass

    def should_we_sync_now(self):
        return True





class SharedParamsRateLimited(SharedParamsAutoSync):

    # Make sure to specify the argument "every_n_batches=T" when you instantiate this extension,
    # or something to that effect to determine how often we want to call it.
    #
    # This extension does the same as SharedParamsAutoSync,
    # but it overrides the `should_we_sync_now` functionality
    # to be able to skip certain updates.

    def __init__(self,
                 maximum_rate=1.0,
                 want_sync_timing_log=False,
                 **kwargs):

        super(SharedParamsRateLimited, self).__init__(**kwargs)

        self.maximum_rate = maximum_rate

        self.sync_start_timestamp = time.time()
        self.sync_end_timestamp = time.time()

        self.rolling_estimate_sync_cost = 0.0
        #self.rolling_estimate_work_cost = 1.0

        # Just a way to add some smoothing to our estimates
        # about the costs to sync, or process stuff outside.
        # Smaller factor -> more smoothing.
        # Has to be in (0.0, 1.0) interval.
        self.decay_factor = 0.2

        # This creates some "pollution" in the quantities reported,
        # but it's useful if you want to get a better understanding
        # of how much time was spent synching.
        self.want_sync_timing_log = want_sync_timing_log


    def presync_callback(self):
        self.sync_start_timestamp = time.time()

    def postsync_callback(self):
        self.sync_end_timestamp = time.time()
        time_diff = self.sync_end_timestamp - self.sync_start_timestamp
        self.rolling_estimate_sync_cost = self.decay_factor * time_diff + (1.0-self.decay_factor) * self.rolling_estimate_sync_cost

        if self.want_sync_timing_log:
            # write down how long the sync took
            current_row = self.main_loop.log.current_row

            current_row['param_sync_start'] = self.sync_start_timestamp
            current_row['param_sync_end'] = self.sync_end_timestamp
            current_row['param_sync_duration'] = time_diff


    def should_we_sync_now(self):
        work_cost_since_last_sync = time.time() - self.sync_end_timestamp

        #time_diff = time.time() - self.sync_end_timestamp
        #self.rolling_estimate_work_cost = self.decay_factor * time_diff + (1.0-self.decay_factor) * self.rolling_estimate_work_cost

        if self.rolling_estimate_sync_cost < self.maximum_rate * work_cost_since_last_sync:
            if self.debug:
                print("Going to perform update with server because %f < %f * %f." % (self.rolling_estimate_sync_cost, self.maximum_rate, work_cost_since_last_sync))

            return True
        else:
            return False
