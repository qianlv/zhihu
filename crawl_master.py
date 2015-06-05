#!/usr/bin/python
#encoding=utf-8 

import sys
import re
import os
import time
import argparse
import logging
logging_format = "%(asctime)s|%(filename)s|%(funcName)s:%(lineno)d|%(levelname)s: %(message)s"
logging.basicConfig(filename = os.path.join(os.getcwd(), "log.txt"), 
                    level = logging.DEBUG,
                    format = logging_format
                    )

import redis
from pybloom import BloomFilter

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

from zhihu.base.database import create_topic_table, create_user_table
from zhihu.base import get_config
import zhihu.setting as setting
from ConfigParser import  NoSectionError

class CrawlMaster(BaseHTTPRequestHandler):
    """ This is class a simple http server 
        to deal with crawler get url and get url.
        use bloomfilter to filter repeated url
        use redis list to keep a queue
    """

    @classmethod
    def init(self, init_dict, clear_data = True, _capacity = 5000000, _error_rate = 0.001):
        """ init BloomFilter and Redis 
            init_dict is a dict
        """
        self.bf = BloomFilter(capacity = _capacity, error_rate = _error_rate)
        self.rd = self.link_redis()
        for que_name, urls in init_dict.items():
            if clear_data:
                self.rd.delete(que_name)
            try:
                for url in urls:
                    if not url in self.bf:
                        self.rd.lpush(que_name, url)
                        self.bf.add(url)
            except redis.ConnectionError, e:
                logging.error("Can't connect to redis server|%s", str(e))
                exit("Can't connet to redis server")

        if clear_data:
            create_user_table()
            create_topic_table()
            
    @classmethod
    def link_redis(self):
        try:
            config = get_config("redis")
            host = config("host")
            port = config("port")
            db   = config("db")
        except (IOError, NoSectionError), e:
            logging.error('You must be set right config.ini|%s', str(e))
            exit("You must be set right config.ini")

        return redis.Redis(host = host, port = port, db = db)

    def get_que_name(self):
        print self.path
        que_name = self.path.split('/')[1:-1]
        print que_name
        return (que_name[0], int(que_name[1]))

    def do_GET(self):
        """ GET method, get url from queue"""
        que_name, _ = self.get_que_name()
        if self.rd.llen(que_name) > 0:
            message = self.rd.rpop(que_name)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(message)
        else:
            self.send_error(400, "queue is empty")
        return

    def do_POST(self):
        """ POST method, post url to queue"""
        import cgi
        form = cgi.FieldStorage(  
            fp=self.rfile,
            headers=self.headers,
            environ={
                'REQUEST_METHOD':'POST',
                'CONTENT_TYPE':self.headers['Content-Type'],
            })
        import json
        url_list = json.loads(form['url'].value)
        response_code = 200
        que_name, que_type = self.get_que_name()
        if url_list:
            if que_type == 0:
                for url in url_list:
                    if not url in self.bf:
                        self.rd.lpush(que_name, url)
                        self.bf.add(url)
            elif que_type == 1:
                print url_list
                for url in url_list:
                    self.rd.lpush(que_name, url)
        else:
            self.send_error(400, "url is error")
            return
            
        self.send_response(response_code)
        return

class MyHTTPServer(HTTPServer):
    """This class is necessary to allow passing custom request handler into
       The CrawlMaster"""
    def __init__(self, server_address, RequestHandlerClass,
                 init_dict, clear_data = True,
                 _capacity = 5000000, _error_rate = 0.001):
        HTTPServer.__init__(self,server_address, RequestHandlerClass)
        RequestHandlerClass.init(init_dict, clear_data, _capacity, _error_rate)

def main():
    config = get_config("http")
    init_dict = {
                'user' : ['e-mo-de-nai-ba', 'gayscript', 'xiaozhibo', 'giantchen', 
                 'jeffz', 'incredible-vczh' 'fenng', 'lawrencelry', 'jixin', 'winter-25'],
                'topic': ['19776749', '19612637']
                }
    server = MyHTTPServer(
            (config('host'), int(config('port'))), 
            CrawlMaster, init_dict
            )

    print 'Start Server, use <Ctrl-C> to stop'
    try:
        server.serve_forever()
    except KeyboardInterrupt, e:
        print 'Stop Server'

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
            setting.set_debug(True if args.debug == 0 else False)
        if args.config:
            setting.set_config_file(args.config)
        main()
    elif args.mode == 'set':
        if args.debug:
            setting.set_debug(True if args.debug == 0 else False)
         


