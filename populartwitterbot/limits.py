from datetime import datetime
from multiprocessing import Process
import logging
from helpers import twython
import time


class LimitManager(Process):

    def __init__(self, *args, **kwargs):
        super(LimitManager, self).__init__(*args, **kwargs)
        self.registered = []
        self.response_limits = {}

    def register(self, access):
        if not self.registered:
            self.synchronize_limits(access)
        self.registered.append(access)

    def keys(self):
        return self.limits.keys()

    def synchronize_limits(self, access):
        limits = access.get_application_rate_limit_status()
        self.limits = limits['resources']
        super_dict = {}
        for d in self.limits.values():
            for k, v in d.iteritems():
                super_dict[k] = v
        self.limits = super_dict
        self.next_sync = datetime.fromtimestamp(
            self.limits.items()[0][1]['reset'])

    def run(self):
        for access in self.registered:
            self.unqueue_endpoints(access)
        time.sleep(0.5)

    def has_available_limit(self, queue_name):
        if queue_name in self.limits:
            limit = self.limits[queue_name]
        elif queue_name in self.response_limits:
            limit = self.response_limits[queue_name]
        else:
            limit = {u'remaining': 1,
                     u'reset': int(datetime.now().strftime('%s'))}
        return ((limit[u'remaining'] and limit[u'remaining'] > 0) or
                (limit[u'reset'] and
                 datetime.fromtimestamp(float(limit[u'reset'])) <
                 datetime.now()))

    @twython
    def send(self, access, request):
        access.send(request)
        queue_name = request[1]
        if queue_name in self.limits:
            self.limits[queue_name][u'remaining'] -= 1
        h_get = access.get_lastfunction_header
        header = lambda k: int(h_get(k)) if h_get(k) else h_get(k)
        temporal = {
            u"limit": header('x-rate-limit-limit'),
            u"remaining": header('x-rate-limit-remaining'),
            u"class": header('x-rate-limit-class'),
            u"reset": header('x-rate-limit-reset')
        }
        if None not in temporal.values():
            self.response_limits[queue_name] = temporal

    def unqueue_endpoints(self, access):
        if self.next_sync < datetime.now():
            self.synchronize_limits(access)
        for queue_name in access.priority_order:
            if self.has_available_limit(queue_name):
                result = True
                with access.locks[queue_name]:
                    unziped_request = access.pop(queue_name)
                    if unziped_request:
                        result = self.send(access, unziped_request)
                if not result:
                    access.push(unziped_request)
