#!/usr/bin/python
#encoding=utf-8

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import re
import json
import os
import logging
logging_format = "%(asctime)s|%(filename)s|%(funcName)s:%(lineno)d|%(levelname)s: %(message)s"
logging.basicConfig(filename = os.path.join(os.getcwd(), "log.txt"), 
                    level = logging.DEBUG,
                    format = logging_format
                    )


from bs4 import BeautifulSoup

from zhihuBase import ZhiHuPage, get_number_from_string
from zhihuBase import ZHI_HU_URL
import answer, question, topic, collection

class User(ZhiHuPage):
    def __init__(self, url, name = None, user_id = None):
        if url and url[-1] == '/':
            url = url[0:-1]
        self.user_name = name
        self.user_id = user_id
        super(User, self).__init__(url)

    # 用户名
    def get_user_name(self):
        if self.url is None:
            self.user_name = u"匿名用户"
        if self.user_name == None:
            try:
                soup = self.soup.find("div", attrs={"class": "title-section ellipsis"})
                self.user_name = soup.span.string
            except Exception, e:
                logging.warn(u"无法获取到用户名|%s|%s", self.url, unicode(e))
                return None
        return self.user_name.encode("utf-8")

    def get_user_id(self):
        return self.get_id()


    # 获得赞同数
    def get_agrees_num(self):
        if self.url is None:
            self.agrees_num = -1

        if hasattr(self, "agrees_num"):
            return self.agrees_num
        else:
            try:
                soup = self.soup.find("span", attrs={"class": "zm-profile-header-user-agree"}).strong
                self.agrees_num = int(soup.string)
            except Exception, e:
                logging.warn(u"无法获取用户获得的赞同数|%s|%s", self.url, unicode(e))
                return None
            
        return self.agrees_num

    # 获得感谢数
    def get_thanks_num(self):
        if self.url is None:
            self.thanks_num = -1

        if hasattr(self, "thanks_num"):
            return self.thanks_num
        else:
            try:
                soup = self.soup.find("span", 
                        attrs={"class": "zm-profile-header-user-thanks"}).strong
                self.thanks_num = int(soup.string)
            except Exception, e:
                logging.warn(u"无法获取用户获得的感谢数|%s|%s", self.url, unicode(e))
                return None
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

        try:
            soup = self.soup.find("div", attrs={"class": "profile-navbar clearfix"})
        except Exception, e:
            logging.warn(u"无法获取用户获得的各类活动数量|%s|%s", self.url, unicode(e))
            return [-1, -1, -1, -1, -1]

        self.action_num = []
        for num in soup.find_all("a")[1:]:
            self.action_num.append(int((num.span.string)))
        return self.action_num
    
    # 关注者人数
    def get_followers_num(self):
        if self.url is None:
            self.followers_num = -1

        if hasattr(self, "followers_num"):
            return self.followers_num
        else:
            try:
                soup = self.soup.find("div", attrs={"class": "zm-profile-side-following zg-clear"})
                self.follower_num = int(soup.find_all("strong")[1].string)
            except Exception, e:
                logging.warn(u"无法获取用户关注者人数|%s|%s", self.url, unicode(e))
                return 0

        return self.follower_num

    # 关注多少人
    def get_followees_num(self):
        if self.url is None:
            self.followees_num = -1

        if hasattr(self, "followees_num"):
            return self.followees_num
        else:
            try:
                soup = self.soup.find("div", attrs={
                        "class": "zm-profile-side-following zg-clear"})
                self.followees_num = int(soup.find_all("strong")[0].string)
            except Exception, e:
                logging.warn(u"无法获取用户关注多少人|%s|%s", self.url, unicode(e))
                return 0

        return self.followees_num

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
            follow_soup = BeautifulSoup(self.get_page(url).content)
            try:
                follow_tag = follow_soup.find("div", attrs={"class": "zh-general-list clearfix"})
                follow_a = follow_tag.find_all("a", attrs={"class": "zm-item-link-avatar"})
                for follow_user in follow_a:
                    url = ZHI_HU_URL + follow_user.get("href")
                    yield User(url)
            except Exception, e:
                logging.warn(u"无法获取用户关注者和被关注者信息|%s|%s|%s", url, self.url, unicode(e))
                yield (url, 0)
                return

            if page_num <= 1:
                return
            try:
                # 初始化data数据
                data_init = json.loads(follow_tag.get("data-init"), encoding='utf-8')
                input_tag = follow_soup.find("input", attrs={"type":"hidden", "name": "_xsrf"})
                value = input_tag.get("value")
                post_url = ZHI_HU_URL + "/node/" + data_init['nodename']
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
                        url = ZHI_HU_URL + follow_user.get('href')
                        yield User(url)
            except Exception, e:
                logging.warn(u"无法获取用户关注者和被关注者信息|%s|%s|%s", post_url, self.url, unicode(e))
                yield (post_url, offset)
                return

    # 关注话题数
    def get_topics_num(self): 
        if self.url is None:
            self.topics_num = -1
        
        if hasattr(self, "topics_num"):
            return self.topics_num
        try:
            url = self.url.replace(ZHI_HU_URL, "") + "/topics"
            
            self.topics_num = get_number_from_string( \
                    self.soup.find("a", href=url).strong.string)[0]
        except Exception, e:
            logging.warn(u"无法获取用户关注话题数|%s|%s", self.url, unicode(e))
            return 0 
        return self.topics_num

    # 关注的话题
    def get_topics(self):
        if self.url is None:
            return
        else:
            post_url = self.url + "/topics"
            num = self.get_topic_num()
            page_num = (num - 1) / 20 + 1
            topic_soup = BeautifulSoup(self.get_page(post_url).content)
            try:
                topic_tag = topic_soup.find("div", 
                            attrs={"id": "zh-profile-topic-list"})
                topic_a = topic_tag.find_all("a", 
                            attrs={"class": "zm-list-avatar-link"})
                for a in topic_a:
                    url = ZHI_HU_URL + a.get("href")
                    #print url
                    yield topic.Topic(url)
            except Exception, e:
                logging.warn(u"无法获取用户关注话题信息|%s|%d|%s|%s", post_url, 0, self.url, unicode(e))
                yield (post_url, 0)
                return 

            if page_num <= 1:
                return
            try:
                # 初始化data数据
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
                        url = ZHI_HU_URL + a.get("href")
                        #print url
                        yield topic.Topic(url)
            except Exception, e:
                logging.warn(u"无法获取用户关注话题|%s|%d|%s|%s", post_url, offset, self.url, unicode(e))
                yield (post_url, offset)
                return 



    # 关注的专栏数
    def get_follow_posts_num(self):
        if self.url is None:
            self.follow_posts_num = -1
        
        if hasattr(self, "follow_posts_num"):
            return self.follow_posts_num

        try:
            url = self.url.replace(ZHI_HU_URL, "") + "/columns/followed"
            print url
            self.follow_posts_num = get_number_from_string(
                        self.soup.find("a", href=url).strong.string)[0]
        except Exception, e:
            logging.warn(u"无法获取用户关注专栏数|%s|%s", self.url, unicode(e))
            return 0
        return self.follow_posts_num

    # 回答的问题
    def get_answers(self):
        if self.url is None:
            return

        page = (self.get_answers_num() + 19) / 20
        for i in range(1, page + 1):
            try:
                get_url = "%s/answers?page=%d" % (self.url, i)
                soup = BeautifulSoup(self.get_page(get_url).content)
                answer_list = soup.find("div", id="zh-profile-answer-list").find_all("a", class_="question_link")
                for item in answer_list:
                    url = ZHI_HU_URL + item.get("href")
                    yield answer.Answer(url)
            except Exception, e:
                logging.warn(u"无法获取用户回答信息|%s|%s|%s", get_url, self.url, unicode(e))
                yield get_url
                return 

    # 提的问题
    def get_asks(self):
        if self.url is None:
            return

        page = (self.get_asks_num() + 19) / 20
        for i in range(1, page + 1):
            try:
                get_url = "%s/asks?page=%d" % (self.url, i)
                soup = BeautifulSoup(self.get_page(get_url).content)
                ask_list = soup.find("div", id="zh-profile-ask-list").find_all("a", class_="question_link")
                for item in ask_list:
                    url = ZHI_HU_URL + item.get("href")
                    yield question.Question(url)
            except Exception, e:
                logging.warn(u"无法获取用户所提问题信息|%s|%s|%s", get_url, self.url, unicode(e))
                yield get_url
                return 

    # 收藏夹
    def get_collections(self):
        if self.url is None:
            return
        
        page = (self.get_collections_num() + 19) / 20
        for i in range(1, page + 1):
            try:
                get_url = "%s/collections?page=%d" % (self.url, i)
                soup = BeautifulSoup(self.get_page(get_url).content)
                collection_list = soup.find_all("a", class_="zm-profile-fav-item-title")
                for item in collection_list:
                    url = ZHI_HU_URL + item.get("href")
                    yield collection.Collection(url)
            except Exception, e:
                logging.warn(u"无法获取用户收藏夹信息|%s|%s|%s", get_url, self.url, unicode(e))
                yield get_url
                return 

class UserBrief(ZhiHuPage):
    def __init__(self, user_id):
        params = {"url_token": user_id}
        params = {"params": json.dumps(params)}
        self.user_id = user_id
        self.url = ZHI_HU_URL + "/node/MemberProfileCardV2"
        self.soup = BeautifulSoup(self.get_page(self.url, params = params).content)

    def get_user_id(self):
        return self.user_id

    def get_user_name(self):
        try:
            self.user_name = self.soup.find("span", \
                            class_ = "name").string
        except AttributeError, e:
            logging.warn("Can't get user name|%s|%s", user_id, str(e))
            return None
        return self.user_name

    
    def get_answers_num(self):
        if hasattr(self, "answers_num"):
            return self.answers_num

        try:
            self.answers_num =self.soup.find_all( \
                            "span", class_ = "value")[0].string 
            self.answers_num = self.deal_num(self.answers_num)
        except (KeyError, AttributeError), e:
            logging.warn("Can't get user's answer num|%s|%s", user_id, str(e))
            return None
        return self.answers_num

    def get_posts_num(self):
        if hasattr(self, "posts_num"):
            return self.posts_num

        try:
            self.posts_num =self.soup.find_all( \
                            "span", class_ = "value")[1].string 
            self.posts_num = self.deal_num(self.posts_num)
        except (KeyError, AttributeError), e:
            logging.warn("Can't get user's post num|%s|%s", user_id, str(e))
            return None
        return self.posts_num

    def get_followers_num(self):
        if hasattr(self, "followers_num"):
            return self.followers_num

        try:
            self.followers_num =self.soup.find_all( \
                            "span", class_ = "value")[2].string 
            self.followers_num = self.deal_num(self.followers_num)
        except (KeyError, AttributeError), e:
            logging.warn("Can't get user's followers num|%s|%s", user_id, str(e))
            return None
        return self.followers_num
    


if __name__ == '__main__':
    #user = User("http://www.zhihu.com/people/wang-yi-zhu-39-58") 
    #user = User("http://www.zhihu.com/people/zen-kou/") 
    #user = User("http://www.zhihu.com/people/mo-zhi/") 
    #user = User("http://www.zhihu.com/people/lishuhang/") 
    #user = User("http://www.zhihu.com/people/chengyuan") 
    #print user.get_user_name()
    #    print followee.get_user_name()
    #for follower in user.get_followers():
    #    print follower.get_user_name()
    #print user.get_action_num()
    #print user.get_topic_num()
    #print user.get_follow_posts_num()
    #count = 0
    #for m_topic in user.get_topics():
    #    count += 1
    #    print count
    #    print m_topic.get_topic_name().encode("utf-8")
    #for ans in user.get_answers():
    #    print ans.get_voter_num()
    #    q = ans.get_question()
    #    print q.get_title()
    #    print '--------'

    #for q in user.get_asks():
    #    print q.get_title()
    #    print q.get_answers_num()
    #    print q.get_follower_num() 

    #for coll in user.get_collections():
    #    print coll.get_collection_name()

    ub = UserBrief("zen-kou")
    print ub.get_user_name()
    print ub.get_answers_num()
    print ub.get_posts_num()
    print ub.get_followers_num()

