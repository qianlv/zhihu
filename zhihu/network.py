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
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

from zhihu.setting import ZHI_HU_URL
from zhihu.setting import COOKIES_DIR, COOKIES_SAVE
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


class NetRequest(object):
    _prixies = None

    def __init__(self, session=None, proxies=None):
        self.logined = False
        self.session = session or requests.session()
        self.proxies = proxies

    def set_login(self):
        self.logined = True

    def set_proxy(self, proxies):
        self.proxies = proxies

    def set_session(self, session):
        self.session = session

    def get_session(self):
        return self.session

    #@check_request
    def post_request(self, url, data=None):
        #if not self.logined:
        #    logger.error("Please Login Zhihu")
        #    sys.exit("Please Login Zhihu")

        headers = get_headers(url)
        time.sleep(randrange(*SLEEP_TIME, _int=float))
        response = self.session.post(url=url,
                                     data=data,
                                     headers=headers,
                                     verify=False,
                                     proxies=self.proxies,
                                     timeout=3)
        response.raise_for_status()
        return response

    #@check_request
    def get_request(self, url, params=None):
        headers = get_headers(url)
        time.sleep(randrange(*SLEEP_TIME, _int=float))
        response = self.session.get(url,
                                    params=params,
                                    headers=headers,
                                    verify=False,
                                    proxies=self.proxies,
                                    timeout=3)
        response.raise_for_status()
        return response

    def save_cookies(self, cookie_file):
        with open(cookie_file, 'w') as f:
            json.dump(self.session.cookies.get_dict(), f)

default_net_request = None

class Login(object):
    """ Login
    """
    def __init__(self, cookie_dir = COOKIES_DIR):
        super(Login, self).__init__()
        self.cookie_dir = cookie_dir

    # 获取验证码
    def save_captcha(self):
        ''' get the picture of captcha and save it on current directory
        '''
        url = ZHI_HU_URL + '/captcha.gif?r=' + str(int(time.time() * 1000))
        response = requests.get(url)

        with response and open('code.gif', 'wb') as f:
            f.write(response.content)

    def login(self, email=EMAIL, passwd=PASSWD):
        global default_net_request
        default_net_request = self._login(email, passwd)

    def _login(self, email=EMAIL, passwd=PASSWD):
        net_request = self._login_by_cookie(email)
        if not net_request:
            net_request = self._login_by_password(email, passwd)
        net_request.set_login()
        return net_request


    def _login_by_cookie(self, email):
        ''' login in zhihu.com by cookie
        '''
        if not email:
            raise ValueError("Lack the email")

        headers = get_headers(ZHI_HU_URL)
        session = requests.session()
        cookie_file = os.path.join(self.cookie_dir, email)

        if os.path.isfile(cookie_file):
            with open(cookie_file, 'r') as f:
                cookies_dict = json.load(f)
                session.headers.update(headers)
                session.cookies.update(cookies_dict)
                return NetRequest(session)
        return None

    def _login_by_password(self, email, passwd):
        ''' login in zhihu.com by acount
        '''
        if not email or not passwd:
            raise ValueError("Lack the email or passwd")

        login_data = {'email': email, 'password': passwd}
        headers = get_headers('http://www.zhihu.com')
        self.save_captcha()

        captcha = raw_input('Please check code.gif to input captcha:')
        login_data['captcha'] = captcha

        net_request = NetRequest()
        net_request.set_login()
        response = net_request.post_request('http://www.zhihu.com/login/email',
                                data=login_data)
        if response is None:
            logger.error(
                "login requests fail!|email:{0}|password:{1}".
                format(self.email, self.passwd))
            sys.exit(
                "login requests fail!|email:{0}|password:{1}".
                format(self.email, self.passwd))

        if response.json()['r'] == 1:
            for m in response.json()['data']:
                logger.error(
                    "Login Failed, reason is: %s",
                    response.json()['data'][m].encode('utf-8')
                )
                sys.exit(response.json()['data'][m].encode('utf-8'))

        cookie_file = os.path.join(self.cookie_dir, email)
        net_request.save_cookies(cookie_file)
        return net_request
