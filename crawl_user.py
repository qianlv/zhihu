#encoding=utf-8

import os
import time
import json
import argparse
import threading
import logging

from zhihu.setting import LOG_FILE, LOG_FORMAT, LOG_LEVEL
logging.basicConfig(filename = LOG_FILE, 
                    level = LOG_LEVEL,
                    format = LOG_FORMAT
                    )

import requests
import zhihu.setting as setting
from zhihu.setting import ZHI_HU_URL, MAX_FAIL_COUNT, get_debug
from zhihu.base.database import CrawlerDb
from zhihu.base import get_config
from zhihu.base.ippools import change_cur_proxies

from zhihu.webparse import user

class CrawlUser(CrawlerDb, threading.Thread):
    def __init__(self):
        super(CrawlUser, self).__init__()
        threading.Thread.__init__(self)
        self.user_info = []
        self.success_count = 0;
        self.count = 0
        config = get_config("http")
        self.http_url = "http://%s:%s/user/" % (str(config('host')), str(config('port')))

    def get_url(self):
        r = requests.get(self.http_url + str(0) + '/')
        if r.status_code == 200:
            return r.content
        elif r.status_code == 400:
            return None

    def post_url(self, url_list, que_type):
        r = requests.post(self.http_url + str(que_type) + '/', data={'url':json.dumps(url_list)})

    def insert_user(self):
        sql = "insert into `user` (`uid`, `agrees`, `thanks`, \
              `asks`, `answers`, `posts`, `collections`, `logs`, \
              `followees`, `followers`, `topics`, `follow_posts`) \
              values "

        insert_sql = reduce(lambda x, y : x + "('%s', %d, %d, %d, %d, %d, \
                     %d, %d, %d, %d, %d, %d)," % y, self.user_info, sql)
        insert_sql = insert_sql[0:-1]
        self.user_info = []
        self.dbexecute(insert_sql)

    def deal(self, uid):
        from urlparse import urljoin
        url = urljoin(ZHI_HU_URL, "people/"+str(uid))

        cur_user = user.User(url, user_id = uid)
        if not cur_user:
            self.post_url([uid,], 1)
            return
        info = (cur_user.get_user_id().replace("'", "''"), cur_user.get_agrees_num(),
                cur_user.get_thanks_num(), cur_user.get_asks_num(),
                cur_user.get_answers_num(), cur_user.get_posts_num(),
                cur_user.get_collections_num(), cur_user.get_logs_num(),
                cur_user.get_followees_num(), cur_user.get_followers_num(),
                cur_user.get_topics_num(), cur_user.get_follow_posts_num(),
                )

        
        for item in info[1:]:
            if item < 0:
                change_cur_proxies()
                self.post_url([uid,], 1)
                return
        if get_debug():
            print url
            print info
        self.user_info.append(info)
        url_list= [url.split('/')[-1] for url, _ in cur_user.get_followees()]
        self.post_url(url_list, 0)
        if len(self.user_info) >= 3:
            self.insert_user()

    def run(self):
        while True:
            uid = self.get_url()
            if not uid is None:
                self.count = 0
                self.deal(uid)
                self.success_count += 1
                if self.success_count > 1000:
                    change_cur_proxies()
            else:
                if self.user_info:
                    self.insert_user()
                logging.info("Queue is Empty|%s|%d", self.getName(), self.count)
                self.count += 1
                time.sleep(1)
            if self.count >= 10:
                break
        logging.info("Thread %s exit", self.getName())

def main():
    threads = [CrawlUser() for i in range(15)]
    for my_thread in threads:
        my_thread.start()
    for my_thread in threads:
        my_thread.join()
    print 'Exiting Main Thread'

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', required=True, 
                        choices=['start', 'set'], 
                        help='work mode')
    parser.add_argument('-d', '--debug', type=int, choices=[0,1],
                        help='open or close debug info')
    parser.add_argument('--config', help='config file')
    args = parser.parse_args()
    if args.mode == 'start':
        if not args.debug is None:
            print args.debug
            if args.debug == 0:
                setting.set_debug(False)
            else:
                setting.set_debug(True)
        if args.config:
            setting.set_config_file(args.config)
        main()
    elif args.mode == 'set':
        if args.debug:
            setting.set_debug(True if args.debug == 0 else False)

