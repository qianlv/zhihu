# encoding=utf-8

import os
import re


def save_page(title, content):
    with open(title.strip(), "wb") as tmpfile:
        tmpfile.write(title + '\n')
        tmpfile.write(content.encode('utf-8'))


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
