#!/usr/bin/python
#encoding=utf-8 

import os
import time
import json
import argparse
import logging
logging_format = "%(asctime)s|%(filename)s|%(funcName)s:%(lineno)d|%(levelname)s: %(message)s"
logging.basicConfig(filename = os.path.join(os.getcwd(), "log.txt"), 
                    level = logging.DEBUG,
                    format = logging_format
                    )

import threading
import requests

from zhihu.base.database import CrawlerDb
from zhihu.base import get_config
from zhihu.setting import ZHI_HU_URL
from zhihu.webparse.topic import TopicNode, Topic

class CrawlTopic(CrawlerDb, threading.Thread):
    def __init__(self):
        CrawlerDb.__init__(self)
        threading.Thread.__init__(self)
        self.edges = []
        self.count = 0
        config = get_config("http")
        self.http_url = "http://%s:%s/topic/" % (str(config('host')), str(config('port')))
                        
    def add_topic(self, tids):
        if not tids:
            return
        sql = "insert into `topic` (`tid`, `tname`, `tfollower`) values "
        for tid, tname, tfollower in tids:
            tname = tname.replace("'", "''")
            value_str = "(%d, '%s', %d)," % (tid, tname, tfollower)
            sql += value_str
        sql = sql[0:-1]
        self.dbexecute(sql)

    def add_edge(self, edges):
        if not edges:
            return
        sql = "insert into `topictree` (`pid`, `cid`) values "
        for (pid, cid) in edges:
            value_str = "(%d, %d)," % (pid, cid)
            sql += value_str
        sql = sql[0:-1]
        self.dbexecute(sql)

    def get_url(self):
        r = requests.get(self.http_url + str(0) + '/')
        print r.url
        if r.status_code == 200:
            return r.content
        elif r.status_code == 400:
            return None

    def post_url(self, url_list, que_type):
        r = requests.post(self.http_url + str(que_type) + '/', data={'url':json.dumps(url_list)})

    def deal(self, pid):
        t_url = ZHI_HU_URL + "/topic/" + str(pid) 
        n_url = t_url + "/organize/entire"
        print t_url, n_url
        cur_topic = Topic(t_url)
        node = TopicNode(n_url)
        
        if not node or not cur_topic :
            self.post_url([pid,], 1)
            return

        tname = node.get_node_name()
        tfollower = cur_topic.get_topic_follower_num()
        if not tname or tfollower == -1:
            self.post_url([pid,], 1)
            return

        self.add_topic([(pid, tname, tfollower)])
        for child in node.get_children_nodes():
            cid = child.get_topic_id()
            self.edges.append((pid, cid,))
            self.post_url([cid], 0)
            if len(self.edges) >= 3:
                self.add_edge(self.edges)
                self.edges= []

    def run(self):
        while True:
            pid = self.get_url()
            print pid
            if not pid is None:
                pid = int(pid)
                self.count = 0
                self.deal(pid)
            else:
                if self.edges:
                    logging.info("pid = %d", os.getpid())
                    self.add_edge(self.edges)
                    self.edges = []
                logging.info("Queue is Empty|%s|%d", self.getName(), self.count)
                self.count += 1
                time.sleep(1)
            if self.count >= 10:
                break

        logging.info("Thread %s exit", self.getName())


def main():
    threads = [CrawlTopic() for i in range(10)]
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
            if args.debug == 0:
                setting.set_debug(False)
            else:
                setting.set_debug(True)
        if args.config:
            setting.set_config_file(args.config)
        main()
    elif args.mode == 'set':
        if args.debug == 0:
            setting.set_debug(False)
        elif args.debug == 1:
            setting.set_debug(True)

