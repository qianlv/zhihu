# encoding=utf-8
# setting

import os
import logging

# 账号
EMAIL = '1054059790@qq.com'
PASSWD = ''

CURRENT_DIR = os.path.abspath('./zhihu')

DEBUG = True

# cookie 配置
COOKIES_SAVE    = True
COOKIES_DIR     = os.path.join(CURRENT_DIR, 'cookies')
COOKIES_PREFIX_FILENAME = 'cookies.json'

# 常量
ZHI_HU_URL  = "http://www.zhihu.com"

# 日志位置
LOG_DIR     = CURRENT_DIR
LOG_FILE    = os.path.join(CURRENT_DIR, 'log.txt')
LOG_FORMAT  = "%(asctime)s|%(filename)s|%(funcName)s:\
            %(lineno)d|%(levelname)s: %(message)s"
LOG_LEVEL   = logging.DEBUG

# 页面访问随机时间间隔
SLEEP_TIME      = [0, 1.5]
# 代理失败次数最小值
PROXIES_FAIL    = 10
# 最小可用代理数
PROXIES_MIN_USE_COUNT = 30

# 最大页面下载错误次数
# 超过更换代理IP
MAX_FAIL_COUNT = 5

# DB
DB_HOST     = '127.0.0.1'
DB_USER     = 'admin'
DB_PASSWD   = 'password'
DB_NAME     = 'zhihu'
