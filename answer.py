#!/usr/bin/python
#encoding=utf-8

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import re
import datetime
import logging

from bs4 import BeautifulSoup
from zhihuBase import ZhiHuPage, get_number_from_string

import question 
import user

class Answer(ZhiHuPage):
    def __init__(self, url, _question = None):
        super(Answer, self).__init__(url)
        if _question:
            self._question = _question

    # 所属问题
    def get_question(self):
        if hasattr(self, "_question"):
            return self._question
        else:
            url = self.url.split("/")[0:-2]
            url = "/".join(url)
            print url
            self._question = question.Question(url)
        return self._question

    # 作者
    def get_auther(self):
        try:
            auther_tag = self.soup.find("h3", 
                            class_="zm-item-answer-author-wrap")
        
            if auther_tag.string == u'匿名用户':
                auther_url = None
            else:
                auther_tag = auther_tag.a
                auther_url = u"http://www.zhihu.com" + auther_tag.get("href")
        except Exception, e:
            logging.warn("Answer get_auther error|%s|%s",self.url, str(e))
            return None
        return user.User(auther_url)
    # 赞同数
    def get_voter_num(self):
        if hasattr(self, "voter_num"):
            return self.voter_num
        else:
            try:
                soup = self.soup.find("div", attrs={"class": "zm-votebar"})
                voter = soup.find("span", attrs={"class": "count"}).string
                if voter[-1] == "K":
                    self.voter_num = int(voter[0:-1]) * 1000
                elif voter[-1] == "W":
                    self.voter_num = int(voter[0:-1]) * 10000
                else:
                    self.voter_num = int(voter)
            except Exception, e:
                logging.warn("Answer get_voter_num error|%s|%s",self.url, str(e))
                return None
        return self.voter_num

    # 回答时间
    def get_answer_time(self):
        if hasattr(self, "answer_time"):
            return self.answer_time
        else:
            try:
                date_tag = self.soup.find("a", 
                            class_="answer-date-link")
                date_list = get_number_from_string(date_tag.string)

                if len(date_list) == 2:
                    self.answer_time = datetime.datetime.now()
                else:
                    self.answer_time = datetime.datetime(*date_list)
            except Exception, e:
                logging.warn("Answer get_answer_time error|%s|%s",self.url, str(e))
                return None

        return self.answer_time

    def get_content(self):
        try:
            soup = self.soup.find("div", class_=" zm-editable-content clearfix")
            text = soup.get_text()
        except Exception, e:
            logging.info("Answer get_content error|%s|%s",self.url, str(e))
            return None
        return text.encode("utf-8")

if __name__ == '__main__':
    answer = Answer("http://www.zhihu.com/question/22808635/answer/43850014")
    this_question = answer.get_question()
    auther = answer.get_auther() 
    print "题目:", this_question.get_title(), this_question.get_detail()
    print "作者:", auther.get_user_name()
    print "赞同数:", answer.get_voter_num()
    print "发布时间:", answer.get_answer_time().strftime("%Y-%m-%d")
    print answer.get_content()
