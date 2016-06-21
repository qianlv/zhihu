#!/usr/bin/python
# encoding=utf-8

import json

from bs4 import BeautifulSoup

from zhihu.network import default_net_request
from zhihu.utility import remove_blank_lines, get_number_from_string
from zhihu.setting import ZHI_HU_URL
import zhihu.topic
import zhihu.answer


class Question(object):
    def __init__(self, url):
        response = default_net_request.get_request(url)
        self.soup = BeautifulSoup(response.content, "lxml")
        self.url = url

    def get_title(self):
        title = self.soup.find("div", id="zh-question-title").get_text()
        title = remove_blank_lines(title)
        title = title
        return title.encode("utf-8")

    def get_detail(self):
        detail_div = self.soup.find("div", id="zh-question-detail").div
        detail = detail_div.get_text()
        detail = remove_blank_lines(detail)
        return detail.encode("utf-8")

    def get_answers_num(self):
        soup = self.soup.find("h3", id="zh-question-answer-num")
        # 0个或1个答案是没有直接显示答案个数
        if soup is None:
            soup = self.soup.find_all(
                "div", attrs={"class": "zm-item-answer "})
            answers_num = len(soup)
        else:
            answers_num = get_number_from_string(unicode(soup.string))[0]

        return answers_num

    def get_answers(self):
        soup = self.soup.find("div", id="zh-question-answer-wrap")
        answer_link = soup.find_all("a", class_="answer-date-link")
        for link in answer_link:
            url = ZHI_HU_URL + link.get("href")
            yield zhihu.answer.Answer(url)

        answer_num = (self.get_answers_num() + 49) / 50
        if answer_num <= 1:
            return
        data_init = json.loads(soup.get("data-init"))
        post_url = ZHI_HU_URL + "/node/" + data_init['nodename']
        input_tag = self.soup.find(
            "input", attrs={"type": "hidden", "name": "_xsrf"})
        value = input_tag.get("value")
        for offset in range(50, answer_num * 50 + 50, 50):
            data_init['params']['offset'] = offset
            data = {
                "_xsrf": value,
                "method": "next",
                "params": json.dumps(data_init["params"])
            }
            response = default_net_request.post_request(post_url, data)
            for content in response.json()['msg']:
                soup = BeautifulSoup(content, "lxml")
                link = soup.find(
                    "a", class_="answer-date-link")
                url = ZHI_HU_URL + link.get("href")
                yield zhihu.answer.Answer(url)

    def get_follower_num(self):
        soup = self.soup.find("div", id="zh-question-side-header-wrap")
        follower_num = get_number_from_string(soup.get_text())[0]
        return follower_num

    def get_topics(self):
        soup = self.soup.find(
            "div", attrs={"class": "zm-tag-editor-labels zg-clear"})
        topic_all = soup.find_all("a")
        for topic_tag in topic_all:
            url = ZHI_HU_URL + topic_tag.get('href')
            yield zhihu.topic.Topic(url)
