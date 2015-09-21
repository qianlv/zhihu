#!/usr/bin/python
#encoding=utf-8

import json
import logging

from bs4 import BeautifulSoup

from zhihu.network import DownloadPage
from zhihu.utility import remove_blank_lines, get_number_from_string
from zhihu.setting import ZHI_HU_URL
import topic
import answer

download_page = DownloadPage.instance()


class Question(object):
    def __init__(self, url):
        response = download_page.get_request(url)
        self.soup = BeautifulSoup(response.content)
        self.url = url

    def get_title(self):
        if hasattr(self, "title"):
            return self.title.encode("utf-8")

        try:
            title_div = self.soup.find("div", id="zh-question-title")
            title = title_div.get_text()
        except AttributeError, e:
            logging.warn("Question get_title error|%s|%s", self.url, str(e))
            return ''
        title = remove_blank_lines(title)
        self.title = title
        return self.title.encode("utf-8")

    def get_detail(self):
        try:
            detail_div = self.soup.find("div", id="zh-question-detail").div
            detail = detail_div.get_text()
        except AttributeError, e:
            logging.warn("Question get_detail error|%s|%s", self.url, str(e))
            return ''

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
        except (AttributeError, KeyError, ValueError), e:
            logging.warn("Question get_answers_num error|%s|%s", self.url, str(e))
            self.answers_num = -1

        return self.answers_num

    def get_answers(self):
        try:
            soup = self.soup.find("div", id="zh-question-answer-wrap")
            answer_link = soup.find_all("a", class_="answer-date-link")
            for link in answer_link:
                url = ZHI_HU_URL + link.get("href")
                yield answer.Answer(url)
        except AttributeError, e:
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
                response = download_page.post_request(post_url, data) 
                for content in response.json()['msg']:
                    soup = BeautifulSoup(content)
                    link = soup.find("a", 
                                class_="answer-date-link")
                    url = ZHI_HU_URL + link.get("href")
                    yield answer.Answer(url)
        except (AttributeError, ValueError, KeyError), e:
            logging.warn("Question get_answers error|%s|%s", self.url, str(e))
            return
        

    def get_follower_num(self): 
        if hasattr(self, "follow_num"): 
            return self.follower_num
        else:
            try:
                soup = self.soup.find("div", id="zh-question-side-header-wrap")
                self.follower_num = get_number_from_string(soup.get_text())[0]
            except (AttributeError, KeyError), e:
                logging.warn("Question get_follower_num error|%s|%s", self.url, str(e))
                self.follower_num = -1
        return self.follower_num

    def get_topics(self):
        try:
            soup = self.soup.find("div", attrs={"class": "zm-tag-editor-labels zg-clear"})
            topic_all = soup.find_all("a") 
            for topic_tag in topic_all:
                url = ZHI_HU_URL + topic_tag.get('href')
                yield topic.Topic(url)
        except AttributeError, e:
            logging.warn("Question get_topics error|%s|%s", self.url, str(e))
            return
