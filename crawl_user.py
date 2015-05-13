#encoding=utf-8

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import re
import os
import time
import logging
logging_format = "%(asctime)s|%(filename)s|%(funcName)s:%(lineno)d|%(levelname)s: %(message)s"
logging.basicConfig(filename = os.path.join(os.getcwd(), "log.txt"), 
                    level = logging.DEBUG,
                    format = logging_format
                    )

import multiprocessing
from zhihuBase import ZHI_HU_URL, CrawlerDb
import user

class CrawlUser(CrawlerDb):
    def __init__(self, root_user = None):
        super(CrawlUser, self).__init__()
        self.que = multiprocessing.Queue
        self.lock = multiprocessing.Lock()
        if root_user is None:
            self.que.put()
        else:
            map(self.que.put, root_user)

    def create_table():

