
import time

from blocks.extensions import SimpleExtension

class Timestamp(SimpleExtension):
    def __init__(self, **kwargs):
        super(Timestamp, self).__init__(**kwargs)

    def do(self, which_callback, *args):
        current_row = self.main_loop.log.current_row
        current_row['datestamp'] = time.strftime("%Y-%m-%d %H:%M")
        current_row['timestamp'] = time.time()


class StopAfterTimeElapsed(SimpleExtension):
    def __init__(self, total_duration, **kwargs):
        super(StopAfterTimeElapsed, self).__init__(**kwargs)
        self.timestamp_start_of_experiment = time.time()
        self.total_duration = total_duration

    def do(self, which_callback, *args):
        if time.time() - self.timestamp_start_of_experiment < self.total_duration:
            pass
        else:
            # a bit abrupt, but it should work fine
            print "Exiting because self.total_duration = %d seconds have elapsed." % self.total_duration
            exit()
