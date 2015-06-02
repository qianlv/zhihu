#!/usr/bin/python
#encoding=utf-8

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import json
import os
import re
import logging


# 常量

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

import requests
logging.getLogger("requests").setLevel(logging.WARNING)

from bs4 import BeautifulSoup


from ConfigParser import SafeConfigParser, NoSectionError
def get_config(sections_name, config_file = "config.ini"):
    def get_key(key):
        f = open(config_file)
        config = SafeConfigParser()
        config.readfp(f)
        return config.get(sections_name, key)
    return get_key

from setting import proxies
import random

def get_random_proxies():
    return random.choice(proxies)


import MySQLdb

def link_db():
    try:
        config = get_config("mysql", config_file = CONFIG_FILE)
        dbname   = config("dbname")
        username = config("username")
        passwd   = config("passwd")
    except (IOError, NoSectionError), e:
        logging.error("You must be set right config.ini|%s", str(e))
        exit("You must be set right config.ini")
    db = MySQLdb.connect("localhost", username, passwd, dbname, charset="utf8")
    return db

def create_user_table():
    db = link_db()
    cursor = db.cursor()
    cursor.execute("drop table if exists user")
    cursor.execute("create table user "
                   "(uid varchar(100) not null,agrees int not null, "
                   "thanks int not null, asks int not null, "
                   "answers int not null, posts int not null, "
                   "collections int not null, logs int not null, "
                   "followees int not null, followers int not null, " 
                   "topics int not null, follow_posts int not null, "
                   "primary key(uid) ) ENGINE = InnoDB" )


def create_topic_table():
    db = link_db()

    cursor = db.cursor()
    cursor.execute("drop table if exists topic")
    cursor.execute("drop table if exists topictree")
    cursor.execute("create table topic "
                   "(tid int not null, "
                   "tname varchar(60) not null, "
                   "primary key(tid) "
                   ") ENGINE = InnoDB ")
    cursor.execute("create table topictree "
                   "(edgeid int not null auto_increment, "
                   "pid int not null, "
                   "cid int not null, "
                   "primary key(edgeid) "
                   ") ENGINE = InnoDB")

class CrawlerDb(object):
    def __init__(self):
        self.db = link_db()
    
    def __del__(self):
        self.db.close()

    def dbcommit(self):
        self.db.commit()

    def dbrollback(self):
        self.db.rollback()

    def dbexecute(self, sql):
        try:
            cursor = self.db.cursor()
            cursor.execute(sql)
            self.dbcommit()
        except Exception, e:
            logging.error("Execute sql fail|%s|%s", str(e), sql)
            self.dbrollback()
    
    def dbsearch(self, sql):
        try:
            cursor = self.db.cursor()
            cursor.execute(sql)
            result = cursor.fetchall()
            return result
        except Exception, e:
            logging.error("search sql fail|%s|%s", sql, str(e))
            return None
            


if __name__ == '__main__':

