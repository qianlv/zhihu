#!/usr/bin/python
#encoding=utf-8

import json
import os
import logging
import time
from random import randrange

import requests
from bs4 import BeautifulSoup

from zhihu.setting import ZHI_HU_URL
from zhihu.setting import COOKIES_DIR, COOKIES_SAVE
from zhihu.setting import COOKIES_PREFIX_FILENAME
from zhihu.setting import SLEEP_TIME, get_debug
from zhihu.base import get_config, save_page
from zhihu.base.ippools import change_cur_proxies, get_cur_proxies, fail_cur_proxies

session = None

def save_captcha():
    ''' get the picture of captcha on current directory
    '''
    from time import time
    url = ZHI_HU_URL + '/captcha.gif?r=' + str(int(time() * 1000))
    global session
    try:
        r = session.get(url) 
    except (requests.Timeout, requests.ConnectionError), e:
        logging.error("%s|%s",str(e), url)
    with open('code.gif', 'wb') as f:
        f.write(r.content)

def login(proxies_flag = True):
    global session
    if session:
        return
    try:
        from ConfigParser import NoSectionError
        config = get_config("acount")
        email = config("email")
        passwd = config("passwd")
    except (IOError, NoSectionError), e:
        logging.error('You must be set right config.ini|%s', str(e))
        exit("You must be set right config.ini")
    login_data = {'email': email, 'password': passwd}
     
    user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
    headers = { 
        'User-agent' : user_agent,
        'Host': 'www.zhihu.com',
        'Referer': 'http://www.zhihu.com',
        'X-Requested-With': 'XMLHttpRequest'
    }

    session = requests.session()
    cookie_file = os.path.join(COOKIES_DIR, COOKIES_PREFIX_FILENAME + email)
    if os.path.isfile(cookie_file):
        with open(cookie_file, 'r') as f:
            cookies_dict = json.load(f)
            session.headers.update(headers)
            session.cookies.update(cookies_dict)
    else:
        save_captcha()
        import subprocess
        p = subprocess.Popen('display code.gif', shell=True, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT)
        captcha = raw_input('Please check code.gif to input captcha:')
        login_data['captcha'] = captcha
        response = session.post('http://www.zhihu.com/login', data = login_data, 
                headers = headers, proxies = get_random_proxies(proxies), 
                verify = False, timeout = 5)

        save_page('login.html', response.content)
        if response.status_code != 200:
            exit("Please check network |%d", response.status_code)
        if response.json()['r'] == 1:
            print 'Login Failed, reason is:'
            for m in response.json()['msg']:
                logging.error("Login Failed, reason is: %s", \
                    response.json()['msg'][m].encode("utf-8"))
                exit(response.json()['msg'][m].encode("utf-8"))
        if not COOKIES_SAVE:
            return
        with open(cookie_file, 'w') as f:
            json.dump(session.cookies.get_dict(), f)
        
class ZhiHuPage(object):
    def __init__(self, url, soup = None):
        self.url = self.__deal_url(url)
        if soup:
            self.soup = soup
        elif url:
            self.soup = self.get_soup(self.get_page(self.url))
        else:
            self.soup = None

    def __get_session(self):
        global session
        if session:
            return
        login()

    def __deal_url(self, url):
        if url == None:
            return None

        if url[-1] == '/':
            url = url[0:-1]
        url = url.split("/")
        if url[0] != "http:":
            url.insert(0, "http:")
        return "/".join(url)

    def deal_num(self, num):
        if num[-1] == 'K':
            num = int(num[0:-1]) * 1000
        elif num[-1] == 'W':
            num = int(num[0:-1]) * 10000
        else:
            num = int(num)
        return num


    def get_id(self):
        if self.url:
            return self.url.split("/")[4]

    def get_soup(self, response):
        try:
            return BeautifulSoup(response.content)
        except AttributeError, e:
            logging.warn("This is url is error %s|%s", self.url, str(e))

    def get_page(self, url, params=None):
        global session
        self.__get_session()
        cur_proxies = get_cur_proxies()
        if get_debug():
            print cur_proxies

        try:
            time.sleep(randrange(*SLEEP_TIME, _int=float))
            response = session.get(url, params=params, 
                                   proxies = cur_proxies,
                                   verify = False, timeout = 1)
            if response.status_code != 200:
                logging.warn("Can't get right webpage|%s|%d",\
                            response.url, response.status_code)
                fail_cur_proxies()
                change_cur_proxies()
                return None
            return response
        except requests.ConnectionError, e:
            logging.error("Network Problem|%s|%s", url, str(e))
        except requests.Timeout, e:
            logging.error("Time out|%s|%s", url, str(e))
        except Exception, e:
            logging.error("Session Get Fail|%s|%s", url, str(e))
        fail_cur_proxies()
        change_cur_proxies()
        return None

    def get_post(self, url, data):
        global session
        self.__get_session()
        cur_proxies = get_cur_proxies()
        if get_debug():
            print cur_proxies
        try:
            user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
            headers = { 
                'User-agent' : user_agent,
                'Host': 'www.zhihu.com',
                'Referer': url,
            }
            time.sleep(randrange(*SLEEP_TIME, _int=float))
            response = session.post(url, data=data, headers=headers, 
                                    proxies = cur_proxies, 
                                    verify = False, timeout = 1)
            if response.status_code != 200:
                logging.warn("Can't get right webpage|%s|%d", \
                            response.url, response.status_code)
                fail_cur_proxies()
                change_cur_proxies()
                return None
            return response 
        except requests.ConnectionError, e:
            logging.error("Network Problem|%s|%s", url, str(e))
        except requests.Timeout, e:
            logging.error("Time out|%s|%s", url, str(e))
        except Exception, e:
            logging.error("Session Post Fail|%s|%s", url, str(e))
        fail_cur_proxies()
        change_cur_proxies()
        return None
    
