# encoding=utf-8

import logging

from functools import wraps
from requests.exceptions import RequestException
from requests.exceptions import Timeout
from requests.exceptions import ConnectionError
from requests.exceptions import HTTPError


def check_request(func):
    @wraps(func)
    def inner(*args, **kwargs):
        try:
            response = func(*args, **kwargs)
        except RequestException, e:
            logging.error("url: %s|%s", args[0], str(e))
            return None
        if response.status_code != 200:
            return None
        return response
    return inner
