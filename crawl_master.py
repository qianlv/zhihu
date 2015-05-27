#!/usr/bin/python
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

import redis
from pybloom import BloomFilter

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

from zhihuBase import get_config
from ConfigParser import  NoSectionError

class CrawlMaster(BaseHTTPRequestHandler):
    """ This is class a simple http server 
        to deal with crawler get url and get url.
        use bloomfilter to filter repeated url
        use redis list to keep a queue
    """

    @classmethod
    def init(self, init_que, init_url, _capacity = 5000000, _error_rate = 0.001):
        """ init BloomFilter and Redis """
        self.bf = BloomFilter(capacity = _capacity, error_rate = _error_rate)
        try:
            config = get_config("redis")
            host = config("host")
            port = config("port")
            db   = config("db")
        except (IOError, NoSectionError), e:
            logging.error('You must be set right config.ini|%s', str(e))
            exit("You must be set right config.ini")

        self.rd = redis.Redis(host = host, port = port, db = db)
        self.url_que = init_que

        try:
            for url in init_url:
                if not url in self.bf:
                    self.rd.delete(self.url_que)
                    self.rd.lpush(self.url_que, url)
                    self.bf.add(url)
        except redis.ConnectionError, e:
            logging.error("Can't connect to redis server|%s", str(e))
            exit("Can't connet to redis server")

    def do_GET(self):
        """ GET method, get url from queue"""
        if self.rd.llen(self.url_que) > 0:
            message = self.rd.rpop(self.url_que)
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
        if url_list:
            for url in url_list:
                if not url in self.bf:
                    self.rd.lpush(self.url_que, url)
                    self.bf.add(url)
        else:
            self.send_error(400, "url is error")
            return
            
        self.send_response(response_code)
        return

class MyHTTPServer(HTTPServer):
    """This class is necessary to allow passing custom request handler into
       The CrawlMaster"""
    def __init__(self, server_address, RequestHandlerClass,
                init_que, init_url, _capacity = 5000000, _error_rate = 0.001):
        HTTPServer.__init__(self,server_address, RequestHandlerClass)
        RequestHandlerClass.init(init_que, init_url, _capacity, _error_rate)

if __name__ == '__main__':
    from zhihuBase import get_config
    config = get_config("http")
    server = MyHTTPServer(
            (config('host'), int(config('port'))), 
            CrawlMaster,
            'user', 
            ['e-mo-de-nai-ba', 'gayscript', 
             'xiaozhibo', 'giantchen', 
             'jeffz', 'incredible-vczh'
             'fenng', 'lawrencelry',
             'jixin', 'winter-25'])

    print 'Start Server, use <Ctrl-C> to stop'
    server.serve_forever()


