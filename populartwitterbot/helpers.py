from twython import TwythonError
import logging


# Twithon decorator to avoid breaking exceptions in some methods
def twython(func):
    def func_wrapper(*args, **kwargs):
        result = False
        try:
            func(*args, **kwargs)
            result = True
        except TwythonError as e:
            logging.info(e)
        return result
    return func_wrapper
