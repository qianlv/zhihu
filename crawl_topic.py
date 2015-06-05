#!/usr/bin/python
#encoding=utf-8 

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

from zhihu.base.database import CrawlerDb
from zhihu.base import get_config
from zhihu.setting import ZHI_HU_URL
from zhihu.webparse.topic import TopicNode

class TopicTree(CrawlerDb):
    def __init__(self, root_id = None):
        super(TopicTree, self).__init__()
        self.error_url = []
        self.edges = []
        self.http_url = str(config('host')) + ':' + str(config('port'))
        
    def add_topic(self, tids):
        if not tids:
            return
        sql = "insert into `topic` (`tid`, `tname`) values "
        for tid, tname in tids:
            tname = tname.replace("'", "''")
            value_str = "(%d, '%s')," % (tid, tname)
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
        r = requests.get(self.http_url)
        if r.status_code == 200:
            return r.content
        elif r.status_code == 400:
            return None

    def post_url(self, url_list):
        r = requests.post(self.http_url, data={'url':json.dumps(url_list)})

    def deal(self, pid, url = None):
        if url is None:
            url = ZHI_HU_URL + "/topic/" + str(pid) + "/organize/entire"
        node = TopicNode(url, topic_id = pid)
        tname = node.get_node_name()
        if tname is None:
            return (False, url)
        self.add_topic([(pid, tname)])
        for child in node.get_children_nodes():
            if isinstance(child, basestring):
                return (False, child)
            cid = child.get_topic_id()
            self.edges.append((pid, cid))
            self.post_url([cid])
            if len(self.edges) >= 1000:
                logging.info("pid = %d", os.getpid())
                self.add_edge(self.edges)
                self.edges= []

        return (True, None)

    def run(self, count):
        while True:
            pid = self.get_url()
            if not pid is None:
                pid = int(pid)
                count = 0
                (ans, url) = self.deal(pid)
                if not ans:
                    self.error_url.append((pid, url))
            elif self.error_url:
                logging.info("deal some error url|%d", len(self.error_url));
                for pid, url in self.error_url:
                    (ans, url) = self.deal(pid, url = url)
                    if not ans:
                        logging.error("The url is problem|%d|%s", pid, url)
                self.error_url = []
            else:
                if self.edges:
                    logging.info("pid = %d", os.getpid())
                    self.add_edge(self.edges)
                    self.edges = []
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
    my_tree = TopicTree() 
    my_tree.process()
