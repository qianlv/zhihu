import os
import random
import re
from ConfigParser import SafeConfigParser, NoSectionError

from zhihu.setting import get_config_file

def get_config(sections_name):
    def get_key(key):
        f = open(get_config_file())
        config = SafeConfigParser()
        config.readfp(f)
        return config.get(sections_name, key)
    return get_key


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
