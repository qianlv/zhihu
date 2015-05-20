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
    def do_GET(self):
        if self.rd.llen(self.url_que) > 0:
            message = self.rd.rpop(self.url_que)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(message)
        else:
            message = "wait a minute"
            self.send_response(400)
            self.end_headers()
            self.wfile.write(message)
        return

    def do_POST(self):
        import cgi
        form = cgi.FieldStorage(  
            fp=self.rfile,
            headers=self.headers,
            environ={
                'REQUEST_METHOD':'POST',
                'CONTENT_TYPE':self.headers['Content-Type'],
            })
        url = form['url'].value
        response_code = 200
        if url:
            if not url in self.bf:
                print url
                self.rd.lpush(self.url_que, url)
                self.bf.add(url)
        else:
            response_code = 400
        self.send_response(response_code)
        return

class MyHTTPServer(HTTPServer):
    """This class is necessary to allow passing custom request handler into
       The CrawlMaster"""
    def __init__(self, server_address, RequestHandlerClass,
                init_que, init_url, _capacity = 5000000, _error_rate = 0.001):
        HTTPServer.__init__(self,server_address, RequestHandlerClass)
        RequestHandlerClass.bf = BloomFilter(capacity = _capacity, error_rate = _error_rate)
        try:
            config = get_config("redis")
            host = config("host")
            port = config("port")
            db   = config("db")
        except (IOError, NoSectionError), e:
            logging.error('You must be set right config.ini|%s', str(e))
            exit("You must be set right config.ini")

        RequestHandlerClass.rd = redis.Redis(host = host, port = port, db = db)
        RequestHandlerClass.url_que = init_que

        try:
            if not init_url in RequestHandlerClass.bf:
                RequestHandlerClass.rd.delete(RequestHandlerClass.url_que)
                RequestHandlerClass.rd.lpush(RequestHandlerClass.url_que, init_url)
                RequestHandlerClass.bf.add(init_url)
        except redis.ConnectionError, e:
            logging.error("Can't connect to redis server|%s", str(e))
            exit("Can't connet to redis server")

if __name__ == '__main__':
    server = MyHTTPServer(
            ('localhost', 8080), 
            CrawlMaster,
            'topic', 
            '19776749')

    print 'Start Server, use <Ctrl-C> to stop'
    server.serve_forever()


