import unittest
from populartwitterbot import Bot
import json
from datetime import datetime
import hashlib
import time
import os


class TestBot(unittest.TestCase):

    def setUp(self):
        if os.path.exists('config.json'):
            with open('config.json') as f:
                config = json.load(f).items()[0]
        if 'CONFIG' in os.environ:
            config = json.loads(os.environ['CONFIG']).items()[0]
        self.bot = Bot(config)
        self.text = 'Testing from github.com/limiear/populartwitterbot.'
        self.text += (" (%s)" % hashlib.md5(str(datetime.now())).
                      digest().encode("base64")[0:5].lower())

    def test_name(self):
        self.assertEquals(self.bot.name, 'solarbot')
        self.assertIn('populartwitterbot00', self.bot.access.keys())
        self.assertIn('populartwitterbot01', self.bot.access.keys())
        self.bot.populartwitterbot00.update_status(status=self.text)
        time.sleep(10)

    def tearDown(self):
        self.bot.shutdown()


if __name__ == '__main__':
    unittest.main()
