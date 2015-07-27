from twython import Twython
import logging
import json
from limits import LimitManager


class Access(object):

    def __init__(self, config, enabled=True):
        self.config = config
        self.twitter = Twython(
            config['api_key'],
            config['api_secret'],
            config['access'],
            config['access_secret'])
        print self.name, enabled
        self.limits = LimitManager(self, enabled)

    @property
    def name(self):
        return self.config['app_name']

    def __getattr__(self, name):
        return getattr(self.twitter, name)

    def close(self):
        self.limits.shutdown()


class Bot(object):

    def __init__(self, config):
        if isinstance(config, str):
            with open(config) as f:
                config = json.loads(f)
            logging.info("Configured from %s." % config)
        self.config = config
        # self.acesses = map(lambda c: Access(c), config['oauth'])
        self.access = [Access(config['oauth'][0])]
