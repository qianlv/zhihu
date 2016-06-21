#!/usr/bin/python
# encoding=utf-8

''' The script parse the content of the html
    about zhihu answer web page'''

import datetime

from bs4 import BeautifulSoup

from zhihu.network import default_net_request
from zhihu.utility import get_number_from_string
from zhihu.setting import ZHI_HU_URL
import zhihu.question
import zhihu.user
import zhihu.topic


class Answer(object):
    def __init__(self, url, _question=None):
        response = default_net_request.get_request(url)
        self.soup = BeautifulSoup(response.content, "lxml")
        self.url = url
        if _question:
            self._question = _question

    # 所属问题
    def get_question(self):
        url = self.url.split("/")[0:-2]
        url = "/".join(url)
        return zhihu.question.Question(url)

    # 回答ID
    def get_answer_id(self):
        return self.get_id()

    def get_id(self):
        return self.url.split('/')[4]

    # 作者
    def get_auther(self):
        auther_tag = self.soup.find("a", class_="zm-item-link-avatar")
        if auther_tag.string == u'匿名用户':
            auther_url = None
        else:
            auther_url = ZHI_HU_URL + auther_tag.get("href")
        return zhihu.user.User(auther_url)

    def get_voter_page(self, get_url=None):
        if get_url is None:
            answer_anchor = self.soup.find(
                "a",
                class_="zg-anchor-hidden").get("name")
            anchor = answer_anchor.split('-')[1]
            get_url = "%s/answer/%s/voters_profile" % (ZHI_HU_URL, anchor)

        return default_net_request.get_request(get_url)

    # 赞同数
    def get_voter_num(self):
        voters_soup = self.get_voter_page()
        voter_num = int(voters_soup.json()['paging']['total'])
        return voter_num

    # 赞同者
    def get_voters(self):
        get_url = None
        while True:
            if get_url == "":
                break
            voter_soup = self.get_voter_page(get_url)
            get_url = ZHI_HU_URL + voter_soup.json()['paging']['next']

            for item in voter_soup.json()['payload']:
                soup = BeautifulSoup(item, "lxml").find('a')
                yield (soup.get('title'), ZHI_HU_URL + soup.get('href'))

    def get_voters_detail(self):
        voters = self.get_voters()
        for voter in voters:
            yield zhihu.user.User(voter[1])

    # 回答时间
    def get_answer_time(self):
        date_tag = self.soup.find("a", class_="answer-date-link")
        date_list = get_number_from_string(date_tag.string)

        if len(date_list) == 2:
            answer_time = datetime.datetime.now()
        else:
            answer_time = datetime.datetime(*date_list)

        return answer_time

    def get_topics_name_and_url(self):
        soup = self.soup.find(
            "div",
            attrs={"class": "zm-tag-editor-labels zg-clear"}
        )
        topic_all = soup.find_all("a")
        return [(item.string, item.get("href")) for item in topic_all]

    # 话题名
    def get_topics(self):
        for _, url in self.get_topics_name_and_url():
            topic_url = ZHI_HU_URL + url
            yield zhihu.topic.Topic(topic_url)

    def get_content(self):
        soup = self.soup.find("div", class_="zm-editable-content clearfix")
        text = soup.get_text()
        return text.encode("utf-8")
