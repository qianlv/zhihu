#!/usr/bin/python
#encoding=utf-8

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import re
import json
from bs4 import BeautifulSoup

from zhihuBase import ZhiHuPage, remove_blank_lines, get_number_from_string
from zhihuBase import ZHI_HU_URL
import topic
import answer

class Question(ZhiHuPage):
    def __init__(self, url):
       super(Question, self).__init__(url) 

    def get_title(self):
        if hasattr(self, "title"):
            return self.title.encode("utf-8")

        try:
            title_div = self.soup.find("div", id="zh-question-title")
            title = title_div.get_text()
        except Exception, e:
            logging.warn("Question get_title error|%s|%s", self.url, str(e))
            return None
        title = remove_blank_lines(title)
        self.title = title
        return self.title.encode("utf-8")

    def get_detail(self):
        try:
            detail_div = self.soup.find("div", id="zh-question-detail").div
            detail = detail_div.get_text()
        except Exception, e:
            logging.warn("Question get_detail error|%s|%s", self.url, str(e))
            return None

        detail = remove_blank_lines(detail)
        return detail.encode("utf-8")

    def get_answers_num(self):
        if hasattr(self, "answers_num"):
            return self.answers_num

        try:
            soup = self.soup.find("h3", id="zh-question-answer-num")
            # 0个或1个答案是没有直接显示答案个数
            if soup is None:
                soup = self.soup.find_all("div", attrs={"class": "zm-item-answer "})
                self.answers_num = len(soup)
            else:
                self.answers_num = get_number_from_string(unicode(soup.string))[0]
        except Exception, e:
            logging.warn("Question get_answers_num error|%s|%s", self.url, str(e))
            return None

        return self.answers_num

    def get_answers(self):
        try:
            soup = self.soup.find("div", id="zh-question-answer-wrap")
            answer_link = soup.find_all("a", class_="answer-date-link")
            for link in answer_link:
                url = ZHI_HU_URL + link.get("href")
                yield answer.Answer(url)
        except Exception, e:
            logging.warn("Question get_answers error|%s|%s", self.url, str(e))
            return

        answer_num = (self.get_answers_num() + 49) / 50
        if answer_num <= 1:
            return
        try:
            data_init = json.loads(soup.get("data-init"))
            post_url = ZHI_HU_URL + "/node/" + data_init['nodename'] 
            input_tag = self.soup.find("input", attrs={"type":"hidden", "name": "_xsrf"})
            value = input_tag.get("value")
            for offset in range(50, answer_num * 50 + 50, 50):
                data_init['params']['offset'] = offset
                data = {
                    "_xsrf": value,
                    "method": "next",
                    "params": json.dumps(data_init["params"])
                    }
                response = self.get_post(post_url, data) 
                for content in response.json()['msg']:
                    soup = BeautifulSoup(content)
                    link = soup.find("a", 
                                class_="answer-date-link")
                    url = ZHI_HU_URL + link.get("href")
                    yield answer.Answer(url)
        except Exception, e:
            logging.warn("Question get_answers error|%s|%s", self.url, str(e))
            return
        

    def get_follower_num(self): 
        if hasattr(self, "follow_num"): 
            return self.follower_num
        else:
            try:
                soup = self.soup.find("div", id="zh-question-side-header-wrap")
                self.follower_num = get_number_from_string(soup.get_text())[0]
            except Exception, e:
                logging.warn("Question get_follower_num error|%s|%s", self.url, str(e))
                return None
        return self.follower_num

    def get_topics(self):
        try:
            soup = self.soup.find("div", attrs={"class": "zm-tag-editor-labels zg-clear"})
            topic_all = soup.find_all("a") 
            for topic_tag in topic_all:
                url = ZHI_HU_URL + topic_tag.get('href')
                yield topic.Topic(url)
        except Exception, e:
            logging.warn("Question get_topics error|%s|%s", self.url, str(e))
            return


if __name__ == '__main__':
    url = u'http://www.zhihu.com/question/22808635'
    problem = Question(url)
    print problem.get_title()
    print problem.get_detail()
    print problem.get_answers_num()
    print problem.get_follower_num()
    topics = problem.get_topics()
    for my_topic in topics:
        print my_topic.get_topic_name()
    count = 0
    for ans in problem.get_answers():
        count +=1
        print '------', count
        print ans.get_auther().get_user_name()

        

