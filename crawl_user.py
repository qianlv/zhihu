#encoding=utf-8

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import re
import os
import time
import json
import logging
logging_format = "%(asctime)s|%(filename)s|%(funcName)s:%(lineno)d|%(levelname)s: %(message)s"
logging.basicConfig(filename = os.path.join(os.getcwd(), "log.txt"), 
                    level = logging.DEBUG,
                    format = logging_format
                    )

import multiprocessing
import requests
from zhihuBase import ZHI_HU_URL, CrawlerDb
import user

class CrawlUser(CrawlerDb):
    def __init__(self, root_user = None):
        super(CrawlUser, self).__init__()
        self.lock = multiprocessing.Lock()
        self.create_table()
        self.user_info = []
        self.error_url = []

    def create_table(self):
        cursor = self.db.cursor()
        cursor.execute("drop table if exists user")
        cursor.execute("create table user "
                       "(uid varchar(100) not null,agrees int not null, "
                       "thanks int not null, asks int not null, "
                       "answers int not null, posts int not null, "
                       "collections int not null, logs int not null, "
                       "followees int not null, followers int not null, " 
                       "topics int not null, follow_posts int not null, "
                       "primary key(uid) ) ENGINE = InnoDB" )

    def get_url(self):
        r = requests.get("http://localhost:8080")
        if r.status_code == 200:
            return r.content
        elif r.status_code == 400:
            return None

    def post_url(self, url_list):
        r = requests.post("http://localhost:8080", data={'url':json.dumps(url_list)})

    def insert_user(self):
        sql = "insert into `user` (`uid`, `agrees`, `thanks`, \
              `asks`, `answers`, `posts`, `collections`, `logs`, \
              `followees`, `followers`, `topics`, `follow_posts`) \
              values "

        insert_sql = reduce(lambda x, y : x + "('%s', %d, %d, %d, %d, %d, \
                     %d, %d, %d, %d, %d, %d)," % y, self.user_info, sql)
        insert_sql = insert_sql[0:-1]
        self.user_info = []
        with self.lock:
            self.dbexecute(insert_sql)


    def deal(self, uid, url = None):
        from urlparse import urljoin
        if url is None:
            url = urljoin(ZHI_HU_URL, "people/"+str(uid))
        print url
        
        cur_user = user.User(url, user_id = uid)
        if not cur_user:
            return (False, url)
        info = (cur_user.get_user_id().replace("'", "''"), cur_user.get_agrees_num(),
                cur_user.get_thanks_num(), cur_user.get_asks_num(),
                cur_user.get_answers_num(), cur_user.get_posts_num(),
                cur_user.get_collections_num(), cur_user.get_logs_num(),
                cur_user.get_followees_num(), cur_user.get_followers_num(),
                cur_user.get_topics_num(), cur_user.get_follow_posts_num(),
                )
        self.user_info.append(info)
        url_list= [url.split('/')[-1] for url, _ in cur_user.get_followees()]
        self.post_url(url_list)
        if len(self.user_info) >= 100:
            self.insert_user()
        return (True, "")


    def run(self, count):
        while True:
            uid = self.get_url()
            if not uid is None:
                count = 0
                (ans, url) = self.deal(uid)
                if not ans:
                    self.error_url.append((uid, url))
            elif self.error_url:
                logging.info("deal some error url|%d", len(self.error_url));
                for uid, url in self.error_url:
                    (ans, url) = self.deal(uid, url = url)
                    if not ans:
                        logging.error("The url is problem|%s", url)
                self.error_url = []
            else:
                if self.user_info:
                    self.insert_user()
                logging.info("Queue is Empty|%d|%d", os.getpid(), count)
                count += 1
                time.sleep(0.1)
            if count == 100:
                break
        logging.info("Process %d exit", os.getpid())

    def process(self):
        num_process = multiprocessing.cpu_count()
        #num_process = 1
        pool = multiprocessing.Pool(processes=num_process,
                    initializer=self.run,
                    initargs=(0,),
                    )
        pool.close()
        pool.join()

if __name__ == '__main__':
    my_user = CrawlUser()
    my_user.process()        

