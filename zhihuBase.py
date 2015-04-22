#!/usr/bin/python
#encoding=utf-8

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import json
import os
import re
import logging

from ConfigParser import SafeConfigParser

# 常量
ZHI_HU_URL = "http://www.zhihu.com"

def save_page(title, content):
    try:
        with open(title.strip(), "wb") as file:
            file.write(title + '\n')
            file.write(content.encode('utf-8'))
    except Exception, e:
        print Exception, ':', e

def remove_blank_lines(text):
    return os.linesep.join(
                    [line for line in text.splitlines() if line.strip()]
                    )

def get_number_from_string(string):
    numbers = re.findall(r'(\d+)', string)
    numbers = [int(number) for number in numbers]
    return numbers

def is_num_by_except(num):
    try:
        int(num)
        return True
    except ValueError:
        return False

import requests
logging.getLogger("requests").setLevel(logging.WARNING)
from bs4 import BeautifulSoup

session = None

def login(email, passwd):
    global session
    login_data = {'email': email, 'password': passwd}

    user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
    headers = { 
        'User-agent' : user_agent,
        'Host': 'www.zhihu.com',
        'Referer': 'http://www.zhihu.com',
        'X-Requested-With': 'XMLHttpRequest'
    }

    s = requests.session()
    response = s.post('http://www.zhihu.com/login', data = login_data, headers = headers)
    if response.json()['r'] == 1:
        print 'Login Failed, reason is:'
        for m in response.json()['msg']:
            logging.error("Login Failed, reason is: %s", \
                response.json()['msg'][m].encode("utf-8"))
            exit(response.json()['msg'][m].encode("utf-8"))

    session = s

class ZhiHuPage(object):
    def __init__(self, url, soup = None):
        self.url = self.__deal_url(url)
        if soup:
            self.soup = soup
        elif url:
            self.soup = self.get_page(self.url)
        else:
            self.soup = None

    def __get_session(self):
        global session
        try:
            f = open("config.ini")
        except IOError, e:
            logging.error("You must be set config.ini|%d|%s", os.getpid(), str(e))
            exit("You must be set config.ini")
        config = SafeConfigParser()
        config.readfp(f)
        email = config.get("acount", "email")
        passwd = config.get("acount", "passwd")

        if session is None:
            login(email, passwd)

    def __deal_url(self, url):
        if url == None:
            return None

        if url[-1] == '/':
            url = url[0:-1]
        url = url.split("/")
        if url[0] != "http:":
            url.insert(0, "http:")
        return "/".join(url)

    def get_id(self):
        if self.url:
            return int(self.url.split("/")[4])

    def get_page(self, url):
        global session
        self.__get_session()
        try:
            response = session.get(url)
            if (response.status_code != 200):
                logging.warn("Can't get right webpage|%s|%d", url, response.status_code)
                return None
            soup = BeautifulSoup(response.content)
            return soup
        except requests.ConnectionError, e:
            logging.error("Network Problem: %s", str(e))
        except requests.Timeout, e:
            logging.error("Time out: %s", str(e))
        except Exception, e:
            logging.error("Session Post Fail: %s", str(e))
        return None

    def get_post(self, url, data):
        global session
        self.__get_session()
        try:
            user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
            headers = { 
                'User-agent' : user_agent,
                'Host': 'www.zhihu.com',
                'Referer': url,
            }
            response = session.post(url, data=data, headers=headers)
            if (response.status_code != 200):
                logging.warn("Can't get right webpage|%s|%d", url, response.status_code)
                return None
            return response 
        except requests.ConnectionError, e:
            logging.error("Network Problem: %s", str(e))
        except requests.Timeout, e:
            logging.error("Time out: %s", str(e))
        except Exception, e:
            logging.error("Session Post Fail: %s", str(e))
        return None

import MySQLdb

class CrawlerDb(object):
    def __init__(self):
        try:
            f = open("config.ini")
        except IOError, e:
            logging.error("You must be set config.ini|%d|%s", os.getpid(), str(e))
            exit("You must be set config.ini")
        config = SafeConfigParser()
        config.readfp(f)
        dbname   = config.get("mysql", "dbname")
        username = config.get("mysql", "username")
        passwd   = config.get("mysql", "passwd")
        print dbname, username, passwd
        self.db = MySQLdb.connect("localhost", username, passwd, dbname, charset="utf8")
    
    def __del__(self):
        self.db.close()

    def dbcommit(self):
        self.db.commit()

    def dbrollback(self):
        self.db.rollback()

    def dbexecute(self, sql):
        try:
            cursor = self.db.cursor()
            cursor.execute(sql)
            self.dbcommit()
        except Exception, e:
            logging.error("Execute sql fail|%s|%s", str(e), sql)
            self.dbrollback()
    
    def dbsearch(self, sql):
        try:
            cursor = self.db.cursor()
            cursor.execute(sql)
            result = cursor.fetchall()
            return result
        except Exception, e:
            logging.error("search sql fail|%s|%s", sql, str(e))
            return None
            


if __name__ == '__main__':
    text = '''anfd

    sjfd
    sfdk


    fdf  
        
        jfsdkf
    '''
    print remove_blank_lines(text)
    print get_number_from_string(u'andf')[0]
