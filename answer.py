#!/usr/bin/python
#encoding=utf-8

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import re
import json
import datetime
import logging

from bs4 import BeautifulSoup
from zhihuBase import ZhiHuPage, get_number_from_string, ZHI_HU_URL

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
            self._question = question.Question(url)
        return self._question

    # 回答ID
    def get_answer_id(self):
        if not hasattr(self, "answer_id"):
            self.answer_id = self.get_id()
        return self.answer_id

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

    def get_voter_page(self, get_url = None):
        if get_url is None:
            try:
                answer_anchor = self.soup.find("a", \
                        class_ = "zg-anchor-hidden").get("name")
                anchor = answer_anchor.split('-')[1]
                get_url = "%s/answer/%s/voters_profile" % (ZHI_HU_URL, anchor)
            except (KeyError, AttributeError), e:
                logging.warn("Can't find anchor|%s|%s",self.url, str(e))
                return None

        return self.get_page(get_url)

    # 赞同数
    def get_voter_num(self):
        if not hasattr(self, "voter_num"):
            voters_soup = self.get_voter_page()
            try:
                self.voter_num = int(voters_soup.json()['paging']['total'])
            except (AttributeError, KeyError), e:
                logging.warn("Can't get voter num|%s|%s", self.url, str(e))
                return None
        return self.voter_num

    # 赞同者
    def get_voters(self):
        get_url = None
        while True:
            if get_url == "":
                break
            voter_soup = self.get_voter_page(get_url)
            get_url = ZHI_HU_URL + voter_soup.json()['paging']['next']
            for item in voter_soup.json()['payload']:
                try:
                    soup = BeautifulSoup(item).find('a')
                    yield (soup.get('title'), ZHI_HU_URL + soup.get('href'))
                except AttributeError, e:
                    logging.warn("Can't get voter|%s|%s", self.url, str(e))
                    return 

    def get_voters_detail(self):
        voters = self.get_voters()
        for voter in voters:
            yield user.User(voter[1], voter[0])

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
    answer = Answer("http://www.zhihu.com/question/28626263/answer/41992632")
    this_question = answer.get_question()
    auther = answer.get_auther() 
    #print "题目:", this_question.get_title(), this_question.get_detail()
    #print "作者:", auther.get_user_name()
    print "赞同数:", answer.get_voter_num()
    print "发布时间:", answer.get_answer_time().strftime("%Y-%m-%d")
    #print answer.get_content()
    for ur in answer.get_voters():
        print ur[0], ur[1]
    for ur in answer.get_voters_detail():
        print ur.get_user_name()
