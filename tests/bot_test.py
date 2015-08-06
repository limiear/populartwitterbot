import unittest
from populartwitterbot import Bot
import json
from datetime import datetime
import hashlib
import time
import os


class TestBot(unittest.TestCase):

    def setUp(self):
        config = ("bot", {
            "oauth": [
                {"app_name": "",
                 "api_key": "",
                 "api_secret": "",
                 "access": "",
                 "access_secret": "",
                 "enabled": False
                 }
            ]
        })
        if os.path.exists('config.json'):
            with open('config.json') as f:
                config = json.load(f).items()[0]
        self.bot = Bot(config)
        self.text = 'Testing from github.com/limiear/populartwitterbot.'
        self.text += (" (%s)" % hashlib.md5(str(datetime.now())).
                      digest().encode("base64")[0:5].lower())

    def test_name(self):
        # self.assertEquals(self.bot.name, 'populartwitterbot00')
        self.bot.populartwitterbot00.update_status(status=self.text)
        time.sleep(10)

    def tearDown(self):
        self.bot.shutdown()


if __name__ == '__main__':
    unittest.main()
