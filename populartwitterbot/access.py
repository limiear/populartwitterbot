from twython import Twython
import logging
import logging.handlers
from queuelib import FifoDiskQueue
import pickle
from multiprocessing import Lock


logger = logging.getLogger('populartwitterbot')
logger.setLevel(logging.INFO)
handler = logging.handlers.RotatingFileHandler(
    "log_populartwitterbot.out", maxBytes=20, backupCount=5)
logger.addHandler(handler)


class Access(object):

    def __init__(self, config, limits):
        self.config = config
        self.api = Twython(
            config['api_key'],
            config['api_secret'],
            config['access'],
            config['access_secret'])
        self.observe(limits)
        self.priority_order = self.limits.keys()
        self.initialize_queues()
        self.wrap(self.api)

    def observe(self, limits):
        self.limits = limits
        self.limits.register(self)

    def wrap(self, api):
        enabled = self.config['enabled']
        self._get = api.get if enabled else self.fake_call
        self._post = api.post if enabled else self.fake_call
        api.get = self.get
        api.post = self.post

    def unwrap(self, api):
        api.get = self._get
        api.post = self._post

    def initialize_queues(self):
        self.qfactory = (lambda endpoint:
                         FifoDiskQueue('./collections/%s' %
                                       endpoint.replace('/', '+')))
        self.queues = dict(map(lambda k: (k, self.qfactory(k)),
                               self.limits.keys()))
        self.locks = dict(map(lambda k: (k, Lock()), self.limits.keys()))

    def guarantee_lock(self, queue_name):
        if queue_name not in self.locks:
            self.locks[queue_name] = Lock()

    def pop(self, queue_name):
        request = self.queues[queue_name].pop()
        if request:
            request = pickle.loads(request)
        return request

    def push(self, params):
        queue_name = params[1]
        self.guarantee_lock(queue_name)
        with self.locks[queue_name]:
            if queue_name not in self.queues:
                self.queues[queue_name] = self.qfactory(queue_name)
                self.priority_order.append(queue_name)
            self.queues[queue_name].push(pickle.dumps(params))

    def get(self, endpoint, params=None, version='1.1'):
        self.push(['get', endpoint, params, version])

    def post(self, endpoint, params=None, version='1.1'):
        self.push(['post', endpoint, params, version])

    def fake_call(self, *args, **kwargs):
        logger.info("%s %s" % (str(args), str(kwargs)))

    @property
    def name(self):
        return self.config['app_name']

    def send(self, request):
        return getattr(self, '_%s' % request[0])(
            request[1],
            request[2],
            request[3])

    def __getattr__(self, name):
        return getattr(self.api, name)

    def close(self):
        for queue in self.queues.values():
            queue.close()
        self.unwrap(self.api)
