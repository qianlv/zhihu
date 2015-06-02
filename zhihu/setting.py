#encoding=utf-8
#setting

import os

CURRENT_DIR = os.path.abspath('./zhihu')
print CURRENT_DIR

# config
CONFIG_DIR = os.path.join(CURRENT_DIR, 'config')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.ini')

# cookie
COOKIES_SAVE = True
COOKIES_DIR = os.path.join(CURRENT_DIR, 'cookies')
COOKIES_PREFIX_FILENAME = 'cookies.json'

# url
ZHI_HU_URL = "http://www.zhihu.com"

#logging
LOG_DIR = CURRENT_DIR
LOG_FILE = os.path.join(CURRENT_DIR, 'log.txt')
