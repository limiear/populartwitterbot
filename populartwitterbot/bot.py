from twython import Twython
import logging
import json
from limits import LimitManager
from queuelib import FifoDiskQueue
import pickle


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

    def pop(self, queue_name):
        request = self.queues[queue_name].pop()
        if request:
            request = pickle.loads(request)
        return request

    def push(self, params):
        endpoint = params[1]
        if endpoint not in self.queues:
            self.queues[endpoint] = self.qfactory(endpoint)
            self.priority_order.append(endpoint)
        self.queues[endpoint].push(pickle.dumps(params))

    def get(self, endpoint, params=None, version='1.1'):
        self.push(['get', endpoint, params, version])

    def post(self, endpoint, params=None, version='1.1'):
        self.push(['post', endpoint, params, version])

    def fake_call(self, *args, **kwargs):
        logging.info(args, kwargs)

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


class Bot(object):

    def __init__(self, config):
        self.name = config[0]
        self.config = config[1]
        self.limits = LimitManager()
        self.access = dict(map(lambda c:
                               (c['app_name'], Access(c, self.limits)),
                               self.config['oauth']))
        self.limits.bootup_engine()

    def shutdown(self):
        self.limits.shutdown_engine()

    def __getattr__(self, name):
        if name in self.access:
            return self.access[name]
        else:
            default = self.access.items()[0][1]
            return getattr(default, name)


class Cluster(object):

    def __init__(self, config):
        if isinstance(config, str):
            with open(config) as f:
                config = json.loads(f)
            logging.info("Configured from %s." % config)
        self.config = config
        self.bots = map(lambda c: Bot(c), config.items())
