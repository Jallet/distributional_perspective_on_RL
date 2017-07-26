# from baselines.common.mpi_running_mean_std import RunningMeanStd
import tf_util as U
import tensorflow as tf
import gym
from distributions import make_pdtype

class CnnPolicy(object):
    recurrent = False
    def __init__(self, name, ob_space, ac_space):
        with tf.variable_scope(name):
            self._init(ob_space, ac_space)
            self.scope = tf.get_variable_scope().name

    def _init(self, ob_space, ac_space):
        assert isinstance(ob_space, gym.spaces.Box)

        self.pdtype = pdtype = make_pdtype(ac_space)
        sequence_length = None

        sy_ob = U.get_placeholder(name="sy_ob", dtype=tf.float32, shape=[sequence_length] + list(ob_space.shape))
        
        obscaled = sy_ob / 255.0

        with tf.variable_scope("pol"):
            x = obscaled
            x = tf.nn.relu(U.conv2d(x, 8, "l1", [8, 8], [4, 4], pad="VALID"))
            x = tf.nn.relu(U.conv2d(x, 16, "l2", [4, 4], [2, 2], pad="VALID"))
            x = U.flattenallbut0(x)
            x = tf.nn.relu(U.dense(x, 128, 'lin', U.normc_initializer(1.0)))
            logits = U.dense(x, pdtype.param_shape()[0], "logits", U.normc_initializer(0.01))
            self.pd = pdtype.pdfromflat(logits)
        with tf.variable_scope("vf"):
            x = obscaled
            x = tf.nn.relu(U.conv2d(x, 8, "l1", [8, 8], [4, 4], pad="VALID"))
            x = tf.nn.relu(U.conv2d(x, 16, "l2", [4, 4], [2, 2], pad="VALID"))
            x = U.flattenallbut0(x)
            x = tf.nn.relu(U.dense(x, 128, 'lin', U.normc_initializer(1.0)))
            self.vpred = U.dense(x, 1, "value", U.normc_initializer(1.0))
            self.vpredz = self.vpred

        self.state_in = []
        self.state_out = []

        stochastic = tf.placeholder(dtype=tf.bool, shape=())
        sy_ac = self.pd.sample() # XXX
        self._act = U.function([stochastic, sy_ob], [sy_ac, self.vpred])

    def act(self, stochastic, sy_ob):
        ac1, vpred1 =  self._act(stochastic, sy_ob[None])
        return ac1[0], vpred1[0]
    def get_variables(self):
        return tf.get_collection(tf.GraphKeys.VARIABLES, self.scope)
    def get_trainable_variables(self):
        return tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES, self.scope)
    def get_initial_state(self):
        return []

