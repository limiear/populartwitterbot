import logging
import json
from limits import LimitManager
from access import Access


class Bot(object):

    def __init__(self, config):
        self.name = config[0]
        self.config = config[1]
        self.limits = LimitManager()
        self.access = dict(map(lambda c:
                               (c['app_name'], Access(c, self.limits)),
                               self.config['oauth']))
        self.limits.start()

    def shutdown(self):
        self.limits.join()

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
