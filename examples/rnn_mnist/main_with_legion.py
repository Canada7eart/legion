
import os
import numpy as np

####################################################
# Make sure that you get different values for the
# random seeds when running Blocks.
# This goes against the way that Blocks is designed
# at the current time, but it's necessary when
# having multiple workers.

if os.environ.has_key('MOAB_JOBARRAYINDEX'):
    np.random.seed(int(os.environ['MOAB_JOBARRAYINDEX']))
    print "Using MOAB_JOBARRAYINDEX to np.random.seed(%d)." % int(os.environ['MOAB_JOBARRAYINDEX'])
else:
    print "Not on helios, or no MOAB_JOBARRAYINDEX present to seed."

s0 = np.random.randint(low=0, high=100000)
s1 = np.random.randint(low=0, high=100000)
import blocks
import blocks.config
import fuel
blocks.config.config.default_seed = s0
fuel.config.default_seed = s1
####################################################


import theano
from theano import tensor
from blocks.model import Model
from blocks.bricks import Linear, Rectifier, Softmax
from blocks.initialization import IsotropicGaussian, Constant, Identity
from blocks.algorithms import GradientDescent
from blocks.extensions.monitoring import TrainingDataMonitoring
from blocks.extensions.monitoring import DataStreamMonitoring
from blocks.extensions.saveload import Checkpoint
from blocks.bricks.cost import CategoricalCrossEntropy, MisclassificationRate
from blocks.main_loop import MainLoop
from blocks.extensions import FinishAfter, Printing, Timing
from blocks.bricks.recurrent import SimpleRecurrent
from blocks.graph import ComputationGraph
from utils import learning_algorithm
from datasets import MNIST
import os


floatX = theano.config.floatX

from legion.blocks_extensions import SharedParamsAutoSync, SharedParamsRateLimited
from legion.blocks_extensions import Timestamp, StopAfterTimeElapsed

# TODO : shuffle the dataset ahead of time to have different workers
#        cover different parts of the dataset

n_epochs = 100000
x_dim = 1
h_dim = 100
o_dim = 10
batch_size = 1000

print 'Building model ...'
# T x B x F
x = tensor.tensor3('x', dtype=floatX)
y = tensor.tensor3('y', dtype='int32')

x_to_h1 = Linear(name='x_to_h1',
                 input_dim=x_dim,
                 output_dim=h_dim)
pre_rnn = x_to_h1.apply(x)
rnn = SimpleRecurrent(activation=Rectifier(),
                      dim=h_dim, name="rnn")
h1 = rnn.apply(pre_rnn)
h1_to_o = Linear(name='h1_to_o',
                 input_dim=h_dim,
                 output_dim=o_dim)
pre_softmax = h1_to_o.apply(h1)
softmax = Softmax()
shape = pre_softmax.shape
softmax_out = softmax.apply(pre_softmax.reshape((-1, o_dim)))
softmax_out = softmax_out.reshape(shape)
softmax_out.name = 'softmax_out'

# comparing only last time-step
cost = CategoricalCrossEntropy().apply(y[-1, :, 0], softmax_out[-1])
cost.name = 'cross_entropy'
error_rate = MisclassificationRate().apply(y[-1, :, 0], softmax_out[-1])
error_rate.name = 'error_rate'

# Initialization
for brick in (x_to_h1, h1_to_o):
    brick.weights_init = IsotropicGaussian(0.01)
    brick.biases_init = Constant(0)
    brick.initialize()
rnn.weights_init = Identity()
rnn.biases_init = Constant(0)
rnn.initialize()

print 'Bulding training process...'
algorithm = GradientDescent(
    cost=cost,
    parameters=ComputationGraph(cost).parameters,
    step_rule=learning_algorithm(learning_rate=1e-6, momentum=0.0,
                                 clipping_threshold=1.0, algorithm='adam'))


cg = ComputationGraph(cost)
params_to_sync = {}
#cg.variables
counter = 0
print "---- cg.parameters ----"
for p in cg.parameters:
    # `p` is of type theano.sandbox.cuda.var.CudaNdarraySharedVariable

    # Warning. This is not as deterministic as we would want.
    # For now, however, we don't have much of a choice.
    new_name = p.name
    while params_to_sync.has_key(new_name):
        counter += 1
        new_name = p.name + ("_%d" % counter)

    params_to_sync[new_name] = p
    print "Parameter %s now referred to as %s." % (p.name, new_name)
    #import pdb; pdb.set_trace()
print "---- --.---------- ----"




# you can change 'adam' to rmsprop

train_stream, valid_stream = MNIST(batch_size=batch_size)

monitor_train_cost = TrainingDataMonitoring([cost, error_rate],
                                            prefix="train",
                                            after_epoch=True)

monitor_valid_cost = DataStreamMonitoring([cost, error_rate],
                                          data_stream=valid_stream,
                                          prefix="valid",
                                          after_epoch=True)


#DataStream.default_stream(train_set, iteration_scheme=ShuffledScheme(train_set.num_examples, batch_size))




saving_path = os.path.join("/rap/jvb-000-aa/data/alaingui/experiments_legion/4workers_3h", "checkpoint_%0.4d" % np.random.randint(low=0, high=100000))
#saving_path = os.path.join( os.getcwd(), "checkpoint_%0.4d" % np.random.randint(low=0, high=100000))

monitor_interval_nbr_batches = 50
maximal_total_duration = 3*60*60

pid = os.getpid()

model = Model(cost)
main_loop = MainLoop(data_stream=train_stream, algorithm=algorithm,
                     extensions=[monitor_train_cost,
                                 monitor_valid_cost,
                                 FinishAfter(after_n_epochs=n_epochs),
                                 #SharedParamsAutoSync(params_to_sync, alpha=0.5, beta=0.5),
                                 SharedParamsRateLimited(params=params_to_sync, every_n_batches=1, alpha=0.5, beta=0.5, maximum_rate=0.25),
                                 Checkpoint(path=saving_path, save_separately=['log'],
                                            every_n_batches=monitor_interval_nbr_batches),
                                 Timing(every_n_batches=monitor_interval_nbr_batches),
                                 Timestamp(every_n_batches=monitor_interval_nbr_batches),
                                 StopAfterTimeElapsed(every_n_batches=1, total_duration=maximal_total_duration),
                                 Printing()],
                     model=model)

print 'Starting training ...'
main_loop.run()


"""

# debug at home
legion main_with_legion.py --instances=1 --debug --debug_devices=gpu0


# on Helios :
legion main_with_legion.py --allocation="jvb-000-ag" --instances=4

legion main_with_legion.py --allocation="jvb-000-ag" --instances=4 --walltime=0:10:00



legion main_with_legion.py --allocation="jvb-000-ag" --instances=4 --walltime=3:00:00

legion main_with_legion.py --allocation="jvb-000-ag" --instances=2 --walltime=3:00:00

"""
