#!/usr/bin/python
# encoding=utf-8

import json
import os
import sys
import logging
import time
from random import randrange
# from functools import partial

import requests
from bs4 import BeautifulSoup

from zhihu.setting import ZHI_HU_URL
from zhihu.setting import COOKIES_DIR, COOKIES_SAVE
from zhihu.setting import COOKIES_PREFIX_FILENAME
from zhihu.setting import SLEEP_TIME
from zhihu.base import save_page
from .decorator import check_request
# from zhihu.base.ippools import change_cur_proxies, get_cur_proxies, \
#     fail_cur_proxies


def get_url_id(url):
    return url.split("/")[4]


def get_headers(url):
    user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
    headers = {
        'User-agent': user_agent,
        'Host': 'www.zhihu.com',
        'Referer': url,
        'X-Requested-With': 'XMLHttpRequest'
    }
    return headers


@check_request
def post_request(session, url, data=None):
    headers = get_headers(url)
    time.sleep(randrange(*SLEEP_TIME, int=float))
    response = session.post(url=url,
                            data=data,
                            headers=headers,
                            verify=False,
                            timeout=1)
    response.raise_for_status()
    return response


@check_request
def get_request(session, url, params=None):
    headers = get_headers(url)
    time.sleep(randrange(*SLEEP_TIME, int=float))
    response = session.get(url,
                           params=params,
                           headers=headers,
                           verify=False,
                           timeout=1)
    response.raise_for_status()
    return response


# 获取验证码
def save_captcha(session):
    ''' get the picture of captcha and save it on current directory
    '''
    url = ZHI_HU_URL + '/captcha.gif?r=' + str(int(time.time() * 1000))
    response = get_request(session, url)

    with response and open('code.gif', 'wb') as f:
        f.write(response.content)


def login(email, passwd):
    ''' login in zhihu.com by account or cookie
    '''

    login_data = {'email': email, 'password': passwd}
    headers = get_headers('http://www.zhihu.com')

    session = requests.session()
    cookie_file = os.path.join(COOKIES_DIR, COOKIES_PREFIX_FILENAME + email)
    if os.path.isfile(cookie_file):
        with open(cookie_file, 'r') as f:
            cookies_dict = json.load(f)
            session.headers.update(headers)
            session.cookies.update(cookies_dict)
    else:
        save_captcha(session)
        # import subprocess
        # subprocess.Popen('display code.gif',
        #                  shell=True,
        #                  stdout=subprocess.PIPE,
        #                  stderr=subprocess.STDOUT)

        # captcha = raw_input('Please check code.gif to input captcha:')
        # login_data['captcha'] = captcha
        response = post_request(session,
                                'http://www.zhihu.com/login/email',
                                data=login_data)
        if response is None:
            logging.error(
                "login requests fail!|email:{0}|password:{1}".
                format(email, passwd))
            sys.exit(
                "login requests fail!|email:{0}|password:{1}".
                format(email, passwd))
        # debug
        save_page('login.html', response.content)

        if response.json()['r'] == 1:
            print 'Login Failed, reason is:'
            for m in response.json()['data']:
                logging.error(
                    "Login Failed, reason is: %s",
                    response.json()['data'][m].encode('utf-8')
                )
                sys.exit(response.json()['data'][m].encode('utf-8'))

        with COOKIES_SAVE and open(cookie_file, 'w') as f:
            json.dump(session.cookies.get_dict(), f)

    return session


class ZhiHuPage(object):
    def __init__(self, url, soup=None):
        self.url = self.__deal_url(url)
        if soup:
            self.soup = soup
        elif url:
            self.soup = self.get_soup(self.get_page(self.url))
        else:
            self.soup = None

    def __get_session(self):
        if self.session is None:
            self.session = login()

    def __deal_url(self, url):
        if url is None:
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
        self.__get_session()
        response = get_request(self.session, url, params=params)
        return response

    def get_post(self, url, data=None):
        self.__get_session()
        response = post_request(self.session, url, data=data)
        return response
