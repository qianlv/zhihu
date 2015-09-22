#!/usr/bin/python
# encoding=utf-8

import json
import os
import sys
import time
import threading
from random import randrange
# from functools import partial

import requests
from bs4 import BeautifulSoup

from zhihu.setting import ZHI_HU_URL
from zhihu.setting import COOKIES_DIR, COOKIES_SAVE
from zhihu.setting import COOKIES_PREFIX_FILENAME
from zhihu.setting import SLEEP_TIME
from zhihu.setting import EMAIL, PASSWD
# from zhihu.decorator import check_request
from zhihu.logger import logger

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


class DownloadPage(object):
    """A download page from web by requests 
    """
    _instance_lock = threading.Lock()
    _prixies = None

    def __init__(self, session=None, proxies=None): 
        self.session = session or requests.session()
        self.proxies = proxies
        self.login()

    @staticmethod
    def instance():
        """ instance a global 'DownLoadPage'
        """
        if not hasattr(DownloadPage, "_instance"):
            with DownloadPage._instance_lock:
                if not hasattr(DownloadPage, "_instance"):
                    DownloadPage._instance = DownloadPage()
        return DownloadPage._instance

    def set_proxy(self, proxies):
        self._proxies = proxies

    #@check_request
    def post_request(self, url, data=None):
        headers = get_headers(url)
        time.sleep(randrange(*SLEEP_TIME, int=float))
        response = self.session.post(url=url,
                                     data=data,
                                     headers=headers,
                                     verify=False,
                                     proxies=self.proxies,
                                     timeout=1)
        response.raise_for_status()
        return response

    #@check_request
    def get_request(self, url, params=None):
        headers = get_headers(url)
        time.sleep(randrange(*SLEEP_TIME, int=float))
        response = self.session.get(url,
                                    params=params,
                                    headers=headers,
                                    verify=False,
                                    proxies=self.proxies,
                                    timeout=1)
        response.raise_for_status()
        return response

    # 获取验证码
    def save_captcha(self):
        ''' get the picture of captcha and save it on current directory
        '''
        url = ZHI_HU_URL + '/captcha.gif?r=' + str(int(time.time() * 1000))
        response = self.get_request(url)

        with response and open('code.gif', 'wb') as f:
            f.write(response.content)

    def login(self):
        if not self.login_by_cookie(EMAIL):
            self.login_by_password(EMAIL, PASSWD)

    def login_by_cookie(self, email):
        ''' login in zhihu.com by cookie
        '''
        if not email:
            raise ValueError("Lack the email or passwd")

        headers = get_headers('http://www.zhihu.com')
        cookie_file = os.path.join(COOKIES_DIR, COOKIES_PREFIX_FILENAME + email)

        if os.path.isfile(cookie_file):
            with open(cookie_file, 'r') as f:
                cookies_dict = json.load(f)
                self.session.headers.update(headers)
                self.session.cookies.update(cookies_dict)
                return True
        return False

    def login_by_password(self, email, passwd):
        ''' login in zhihu.com by acount
        '''
        if not email or not passwd:
            raise ValueError("Lack the email or passwd")

        login_data = {'email': email, 'password': passwd}
        headers = get_headers('http://www.zhihu.com')
        save_captcha()

        captcha = raw_input('Please check code.gif to input captcha:')
        login_data['captcha'] = captcha
        response = post_request('http://www.zhihu.com/login/email',
                                data=login_data)
        if response is None:
            logger.error(
                "login requests fail!|email:{0}|password:{1}".
                format(email, passwd))
            sys.exit(
                "login requests fail!|email:{0}|password:{1}".
                format(email, passwd))

        if response.json()['r'] == 1:
            for m in response.json()['data']:
                logger.error(
                    "Login Failed, reason is: %s",
                    response.json()['data'][m].encode('utf-8')
                )
                sys.exit(response.json()['data'][m].encode('utf-8'))

        with COOKIES_SAVE and open(cookie_file, 'w') as f:
            json.dump(self.session.cookies.get_dict(), f)


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
            logger.warn("This is url is error %s|%s", self.url, str(e))

    def get_page(self, url, params=None):
        self.__get_session()
        response = get_request(self.session, url, params=params)
        return response

    def get_post(self, url, data=None):
        self.__get_session()
        response = post_request(self.session, url, data=data)
        return response
