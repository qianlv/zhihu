#!/usr/bin/python
#encoding=utf-8

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import json
import os
import re

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
        for m in r.json()['msg']:
            print r.json()['msg'][m]

    session = s

class ZhiHuPage(object):
    def __init__(self, url, soup = None):
        if url and url[-1] == '/':
            url = url[0:-1]
        self.url = url
        if soup:
            self.soup = soup
        elif url:
            self.soup = self.get_page(self.url)
        else:
            self.soup = None

    def __get_session(self):
        global session
        email = "1054059790@qq.com"
        passwd = "xiao105405"
        if session is None:
            login(email, passwd)


    def get_page(self, url):
        global session
        self.__get_session()
        try:
            response = session.get(url)
            soup = BeautifulSoup(response.content)
        except requests.ConnectionError:
            print 'Network Problem'
            soup = None
        except requests.Timeout:
            print 'Request times out'
            soup = None
        return soup
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
            return response 
        except requests.ConnectionError:
            print 'Network Problem'
        except requests.Timeout:
            print 'Request times out'
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
