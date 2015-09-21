# encoding=utf-8

import os
import re
from ConfigParser import SafeConfigParser
from zhihu.setting import get_config_file


def save_page(title, content):
    try:
        with open(title.strip(), "wb") as file:
            file.write(title + '\n')
            file.write(content.encode('utf-8'))
    except Exception, e:
        print Exception, ':', e


def remove_blank_lines(text):
    return os.linesep.join([line for line in text.splitlines()
                            if line.strip()])


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
