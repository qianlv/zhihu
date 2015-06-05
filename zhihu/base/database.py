#encoding=utf-8

import logging
from zhihu.base import get_config
from ConfigParser import NoSectionError

import MySQLdb

def link_db():
    try:
        config = get_config("mysql")
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
    cursor.execute("drop table if exists user_test")
    cursor.execute("create table user_test "
                   "(uid varchar(100) not null,agrees int not null, "
                   "thanks int not null, asks int not null, "
                   "answers int not null, posts int not null, "
                   "collections int not null, logs int not null, "
                   "followees int not null, followers int not null, " 
                   "topics int not null, follow_posts int not null, "
                   "primary key(uid) ) ENGINE = InnoDB" )
    db.commit()
    db.close()

def create_topic_table():
    db = link_db()
    cursor = db.cursor()
    cursor.execute("drop table if exists topic")
    cursor.execute("drop table if exists topictree")
    cursor.execute("create table topic "
                   "(tid int not null, "
                   "tname varchar(60) not null, "
                   "tfollower int(11) not null, "
                   "primary key(tid) "
                   ") ENGINE = InnoDB ")
    cursor.execute("create table topictree "
                   "(edgeid int not null auto_increment, "
                   "pid int not null, "
                   "cid int not null, "
                   "primary key(edgeid) "
                   ") ENGINE = InnoDB")
    db.commit()
    db.close()

def create_answer_table():
    db = link_db()
    cursor = db.cursor()
    cursor.execute("drop table if exists answer")
    cursor.execute("create table answer "
                   "(aid int not null, "
                   "uid varchar(60) not null, "
                   "qid int not null, "
                   "voter int not null, "
                   "primary key(qid, aid)"
                   ") ENGINE = InnoDB ")
    db.commit()
    db.close()

def create_question_table():
    db = link_db()
    cursor = db.cursor()
    cursor.execute("drop table if exists question")
    cursor.execute("create table answer "
                   "(qid int not null, "
                   ""
                   ") ENGINE = InnoDB ")
    db.commit()
    db.close()


def create_question_table():
    pass

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
            
