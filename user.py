#!/usr/bin/python
#encoding=utf-8


import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import re
import json

from bs4 import BeautifulSoup
from zhihuBase import ZhiHuPage, get_number_from_string
import answer
import question
import topic


class User(ZhiHuPage):
    def __init__(self, url):
        if url and url[-1] == '/':
            url = url[0:-1]
        super(User, self).__init__(url)

    # 用户名
    def get_user_name(self):
        if self.url is None:
            self.user_name = u"匿名用户"

        if hasattr(self, "user_name"):
            return self.user_name
        else:
            soup = self.soup.find("div", attrs={"class": "title-section ellipsis"})
            self.user_name = soup.span.string
        return self.user_name

    # 获得赞同数
    def get_agree_num(self):
        if self.url is None:
            self.agree_num = -1

        if hasattr(self, "agree_num"):
            return self.agree_num
        else:
            soup = self.soup.find("span", attrs={"class": "zm-profile-header-user-agree"}).strong
            self.agree_num = int(soup.string)
        return self.agree_num

    # 获得感谢数
    def get_thanks_num(self):
        if self.url is None:
            self.thanks_num = -1

        if hasattr(self, "thanks_num"):
            return self.thanks_num
        else:
            soup = self.soup.find("span", 
                    attrs={"class": "zm-profile-header-user-thanks"}).strong
            self.thanks_num = int(soup.string)
        return self.thanks_num

    # 提问数
    def get_asks_num(self):
        return self.get_action_num()[0]

    # 回答数
    def get_answers_num(self):
        return self.get_action_num()[1]

    # 专栏文章数
    def get_posts_num(self):
        return self.get_action_num()[2]
    
    # 收藏数
    def get_collections_num(self):
        return self.get_action_num()[3]
    
    # 公共编辑数
    def get_logs_num(self):
        return self.get_action_num()[4]
        
    # 上面5个活动的数量
    def get_action_num(self):
        if self.url is None:
            self.action_num = [-1, -1, -1, -1, -1]
        if hasattr(self, "action_num"):
            return self.action_num
        soup = self.soup.find("div", attrs={"class": "profile-navbar clearfix"})
        self.action_num = []
        for num in soup.find_all("a")[1:]:
            self.action_num.append(int((num.span.string)))
        return self.action_num
    
    # 关注者人数
    def get_follower_num(self):
        if self.url is None:
            self.follower_num = -1

        if hasattr(self, "follower_num"):
            return self.follower_num
        else:
            soup = self.soup.find("div", attrs={"class": "zm-profile-side-following zg-clear"})
            self.follower_num = int(soup.find_all("strong")[1].string)
        return self.follower_num

    # 关注多少人
    def get_followee_num(self):
        if self.url is None:
            self.followee_num = -1

        if hasattr(self, "followee_num"):
            return self.followee_num
        else:
            soup = self.soup.find("div", attrs={
                    "class": "zm-profile-side-following zg-clear"})
            self.followee_num = int(soup.find_all("strong")[0].string)

        return self.followee_num

    # 获取我关注的人信息
    def get_followees(self):
        return self.__get_followees_or_follwers(
                self.url + "/followees", self.get_followee_num())

    # 获取关注我的人的信息
    def get_followers(self):
        return self.__get_followees_or_follwers(
                self.url + "/followers", self.get_follower_num())

    def __get_followees_or_follwers(self, url, num):
        if self.url is None:
            yield
        else:
            page_num = (num - 1) / 20 + 1
            follow_soup = self.get_page(url) 
            follow_tag = follow_soup.find("div", attrs={"class": "zh-general-list clearfix"})
            follow_a = follow_tag.find_all("a", attrs={"class": "zm-item-link-avatar"})
            for follow_user in follow_a:
                url = "http://www.zhihu.com" + follow_user.get("href")
                yield User(url)

            # 初始化data数据
            if page_num > 1:
                data_init = json.loads(follow_tag.get("data-init"), encoding='utf-8')
                input_tag = follow_soup.find("input", attrs={"type":"hidden", "name": "_xsrf"})
                value = input_tag.get("value")
                post_url = "http://www.zhihu.com/node/" + data_init['nodename']
                for offset in range(20, page_num * 20 + 20, 20):
                    data_init["params"]["offset"] = offset
                    data = {
                        "_xsrf": value,
                        "method": "next",
                        "params": json.dumps(data_init["params"])
                        }
                    response = self.get_post(post_url, data) 
                    for content in response.json()['msg']:
                        soup = BeautifulSoup(content)
                        follow_user = soup.find("a")
                        url = "http://www.zhihu.com" + follow_user.get('href')
                        yield User(url)

    # 关注话题数 
    def get_topic_num(self): 
        if self.url is None:
            self.topic_num = -1
        
        if hasattr(self, "topic_num"):
            return self.topic_num

        soup = self.soup.find_all("div", 
                attrs={"class": "zm-profile-side-section"})[2]
        self.topic_num = get_number_from_string(
                    soup.div.div.a.strong.string)[0]
        return self.topic_num

    # 关注的话题
    def get_topics(self):
        if self.url is None:
            return
        else:
            post_url = self.url + "/topics"
            num = self.get_topic_num()
            page_num = (num - 1) / 20 + 1
            topic_soup = self.get_page(post_url) 
            topic_tag = topic_soup.find("div", 
                        attrs={"id": "zh-profile-topic-list"})
            topic_a = topic_tag.find_all("a", 
                        attrs={"class": "zm-list-avatar-link"})
            for a in topic_a:
                url = "http://www.zhihu.com" + a.get("href")
                #print url
                yield topic.Topic(url)

            # 初始化data数据
            if page_num > 1:
                input_tag = topic_soup.find("input", attrs={"type":"hidden", "name": "_xsrf"})
                value = input_tag.get("value")
                for offset in range(20, page_num * 20 + 20, 20):
                    data = {
                        "_xsrf": value,
                        "offset": offset,
                        "start": 0
                        }
                    response = self.get_post(post_url, data) 
                    content = response.json()['msg'][1]
                    soup = BeautifulSoup(content)
                    topic_a = soup.find_all("a", 
                                attrs={"class": "zm-list-avatar-link"})
                    for a in topic_a:
                        url = "http://www.zhihu.com" + a.get("href")
                        #print url
                        yield topic.Topic(url)



    def get_follow_posts_num(self):
        if self.url is None:
            self.follow_posts_num = -1
        
        if hasattr(self, "follow_posts_num"):
            return self.follow_posts_num

        soup = self.soup.find_all("div", 
                attrs={"class": "zm-profile-side-section"})[1]
        self.follow_posts_num = get_number_from_string(
                    soup.div.div.a.strong.string)[0]
        return self.follow_posts_num

    # 回答的问题
    def get_answers(self):
        if self.url is None:
            return

        page = (self.get_answers_num() + 19) / 20
        for i in range(1, page + 1):
            soup = self.get_page(self.url + "/answers?page=" + str(i))
            answer_list = soup.find("div", id="zh-profile-answer-list").find_all("a", class_="question_link")
            for item in answer_list:
                url = "http://www.zhihu.com" + item.get("href")
                yield answer.Answer(url)

    # 提的问题
    def get_asks(self):
        if self.url is None:
            yield

        page = (self.get_asks_num() + 19) / 20
        for i in range(1, page + 1):
            soup = self.get_page(self.url + "/asks?page=" + str(i))
            ask_list = soup.find("div", id="zh-profile-ask-list").find_all("a", class_="question_link")
            for item in ask_list:
                url = "http://www.zhihu.com" + item.get("href")
                yield question.Question(url)


if __name__ == '__main__':
    #user = User("http://www.zhihu.com/people/wang-yi-zhu-39-58") 
    #user = User("http://www.zhihu.com/people/zen-kou/") 
    #user = User("http://www.zhihu.com/people/mo-zhi/") 
    user = User("http://www.zhihu.com/people/lishuhang/") 
    #print user.get_user_name()
    #print user.get_agree_num()
    #print user.get_thanks_num()
    #print user.get_follower_num()
    #print user.get_followee_num()
    #print user.get_followees()
    #for followee in user.get_followees():
    #    print followee.get_user_name()
    #for follower in user.get_followers():
    #    print follower.get_user_name()
    #print user.get_action_num()
    #print user.get_topic_num()
    #print user.get_follow_posts_num()
    #print user.get_topic_num()
    count = 0
    for m_topic in user.get_topics():
        count += 1
        print count
        print m_topic.get_topic_name()
    #for ans in user.get_answers():
    #    print ans.get_voter_num()
    #    q = ans.get_question()
    #    print q.get_title()
    #    print '--------'

    #for q in user.get_asks():
    #    print q.get_title()
    #    print q.get_answers_num()
    #    print q.get_follower_num() 

