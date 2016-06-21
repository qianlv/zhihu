# encoding=utf-8

import logging
from zhihu.setting import LOG_FILE
from zhihu.setting import LOG_FORMAT
from zhihu.setting import LOG_LEVEL

logging.basicConfig(
    filename=LOG_FILE, 
    format=LOG_FORMAT,
    level=LOG_LEVEL
)

logger = logging.getLogger('zhihu')

