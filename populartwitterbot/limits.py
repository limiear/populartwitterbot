from queuelib import FifoDiskQueue
from datetime import datetime
import threading
import logging
import pickle
from helpers import twython


class LimitManager(object):

    def __init__(self, access, enabled):
        self.access = access
        self.api = access.twitter
        self.response_limits = {}
        self.synchronize_limits()
        self.initialize_queues()
        self.wrap(self.api, enabled)

    @property
    def limits(self):
        return LimitManager.limits

    @limits.setter
    def limits(self, value):
        # The limits are shared between all the instances.
        # Maybe there is a need for a Lock when set or get.
        LimitManager.limits = value

    def initialize_queues(self):
        self.qfactory = (lambda endpoint:
                         FifoDiskQueue('./collections/%s' %
                                       endpoint.replace('/', '+')))
        self.queues = dict(map(lambda k: (k, self.qfactory(k)),
                               self.limits.keys()))
        self.priority_order = self.queues.keys()
        self.engine = threading.Thread(target=self.engine_loop)
        self.running = True
        self.engine.start()

    def synchronize_limits(self):
        limits = self.api.get_application_rate_limit_status()
        with open('limits.json', 'wb') as f:
            pickle.dump(limits, f)
        self.limits = limits['resources']
        super_dict = {}
        for d in self.limits.values():
            for k, v in d.iteritems():
                super_dict[k] = v
        self.limits = super_dict
        self.next_sync = datetime.fromtimestamp(
            self.limits.items()[0][1]['reset'])

    def engine_loop(self):
        while self.running:
            self.unqueue_endpoints()

    def has_available_limit(self, queue_name):
        if queue_name in self.limits:
            limit = self.limits[queue_name]
        elif queue_name in self.response_limits:
            limit = self.response_limits[queue_name]
        else:
            limit = {'remaining': 1}
        return (limit['remaining'] > 0 or
                datetime.fromtimestamp(limit['reset']) < datetime.now())

    @twython
    def send(self, request):
        queue_name = request[1]
        getattr(self, '_%s' % request[0])(
            request[1],
            request[2],
            request[3])
        if queue_name in self.limits:
            self.limits[queue_name][u'remaining'] -= 1
        h_get = self.api.get_lastfunction_header
        header = lambda k: int(h_get(k)) if h_get(k) else h_get(k)
        self.response_limits[queue_name] = {
            "limit": header('x-rate-limit-limit'),
            "remaining": header('x-rate-limit-remaining'),
            "class": header('x-rate-limit-class'),
            "reset": header('x-rate-limit-reset')
        }
        print queue_name, self.response_limits[queue_name]

    def unqueue_endpoints(self):
        if self.next_sync < datetime.now():
            self.synchronize_limits()
        for queue_name in self.priority_order:
            if self.has_available_limit(queue_name):
                request = self.queues[queue_name].pop()
                if request:
                    unziped_request = pickle.loads(request)
                    result = self.send(unziped_request)
                    if not result:
                        self.queues[queue_name].push(request)

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

    def wrap(self, api, enabled):
        self._get = api.get if enabled else self.fake_call
        self._post = api.post if enabled else self.fake_call
        api.get = self.get
        api.post = self.post

    def unwrap(self, api):
        api.get = self._get
        api.post = self._post

    def shutdown(self):
        self.running = False
        self.engine.join()
        for queue in self.queues.values():
            queue.close()
        self.unwrap(self.api)
