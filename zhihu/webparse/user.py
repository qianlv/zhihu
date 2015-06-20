#!/usr/bin/python
#encoding=utf-8

import json
import logging

from bs4 import BeautifulSoup

from zhihu.base.network import ZhiHuPage
from zhihu.base import get_number_from_string
from zhihu.setting import ZHI_HU_URL
import answer, question, topic, collection

class User(ZhiHuPage):
    ''' Parse zhihu the web page of user.
        User(url, [name, user_id])
        url: the url of user.
        name: the name of user.
        user_id: the id of user.
    '''
    def __init__(self, url, name = None, user_id = None):
        if url and url[-1] == '/':
            url = url[0:-1]
        super(User, self).__init__(url)

    def __nonzero__(self):
        if self.url is None or self.soup is None:
            return False
        return True

    def get_user_name(self):
        ''' return the name of user, return None when user doesn't exist.
        '''
        try:
            soup = self.soup.find("div", attrs={"class": "title-section ellipsis"})
            user_name = soup.span.string
        except AttributeError, e:
            logging.warn(u"无法获取到用户名|%s|%s", self.url, str(e))
            return None

        return user_name.encode("utf-8")

    def get_user_id(self):
        ''' Return the id of user '''
        return self.get_id()

    def get_upvote_num(self):
        ''' Return upvote(up vote) number of user.'''
        try:
            soup = self.soup.find("span", attrs={"class": "zm-profile-header-user-agree"}).strong
            agrees_num = int(soup.string)
        except (ValueError, AttributeError), e:
            logging.warn(u"无法获取用户获得的赞同数|%s|%s", self.url, str(e))
            return None

        return agrees_num

    def get_thanks_num(self):
        ''' Return thanks number of user.'''
        try:
            soup = self.soup.find("span", 
                    attrs={"class": "zm-profile-header-user-thanks"}).strong
            thanks_num = int(soup.string)
        except (ValueError,AttributeError), e:
            logging.warn(u"无法获取用户获得的感谢数|%s|%s", self.url, str(e))
            return None

        return thanks_num

    def get_asks_num(self):
        ''' Return ask number of user.'''
        return self.get_action_num()[0]

    def get_answers_num(self):
        ''' Return answers number of user.'''
        return self.get_action_num()[1]

    # 专栏文章数
    def get_posts_num(self):
        ''' Return post number of user.'''
        return self.get_action_num()[2]
    
    def get_collections_num(self):
        ''' Return collection number of user. '''
        return self.get_action_num()[3]
    
    def get_logs_num(self):
        ''' Return log number of user. '''
        return self.get_action_num()[4]
        
    def get_action_num(self):
        if hasattr(self, "action_num"):
            return self.action_num

        self.action_num = []
        try:
            soup = self.soup.find("div", attrs={"class": "profile-navbar clearfix"})
            for num in soup.find_all("a")[1:]:
                self.action_num.append(int((num.span.string)))
        except (AttributeError, KeyError, ValueError), e:
            logging.warn(u"无法获取用户获得的各类活动数量|%s|%s", self.url, str(e))
            self.action_num = [None, None, None, None, None]
        return self.action_num 
    
    def get_followers_num(self):
        ''' Return follower number of user.'''
        try:
            soup = self.soup.find("div", attrs={"class": "zm-profile-side-following zg-clear"})
            follower_num = int(soup.find_all("strong")[1].string)
        except (AttributeError, KeyError), e:
            logging.warn(u"无法获取用户关注者人数|%s|%s", self.url, unicode(e))
            return None

        return follower_num

    def get_followees_num(self):
        ''' Return the number of user which current user follow.'''
        try:
            soup = self.soup.find("div", attrs={
                    "class": "zm-profile-side-following zg-clear"})
            followees_num = int(soup.find_all("strong")[0].string)
        except (AttributeError, KeyError), e:
            logging.warn(u"无法获取用户关注多少人|%s|%s", self.url, unicode(e))
            return None

        return followees_num

    # 获取我关注的人信息
    def get_followees(self, threshold = 2):
        ''' Return iterable of user (url, name) which current user follow.
            threshold is to filter some user which the number of follower, 
            ask, answer, upvote more than 0 less than threshold.
        '''
        return self.__get_followees_or_follwers(
                self.url + "/followees", self.get_followees_num(), threshold)

    def get_followees_user(self, threshold = 2):
        ''' Return iterable of User class which current user follow.
            threshold is to filter some user which the number of follower, 
            ask, answer, upvote more than 0 less than threshold.
        '''
        followees_iter = self.get_followees(threshold)
        for url, name in followees_iter:
            yield user.User(url, name = name)

    def get_followers(self, threshold = 2):
        ''' Return iterable of user (url, name) which follow current user.
            threshold is to filter some user which the number of follower, 
            ask, answer, upvote more than 0 less than threshold.
        '''
        return self.__get_followees_or_follwers(
                self.url + "/followers", self.get_followers_num(), threshold)

    # 获取关注我的人的信息
    def get_followers_user(self, threshold = 2):
        ''' Return iterable of User which follow current user.
            threshold is to filter some user which the number of follower, 
            ask, answer, upvote more than 0 less than threshold.
        '''
        followers_iter = self.get_followers(threshold)
        for url, name in followers_iter:
            yield user.User(url, name = name)

    def __get_followees_or_follwers(self, url, num, threshold):
        if num is None or num <= 0:
            return

        # 判断这个用户是否符合条件
        def check(all_a_tag):   
            threshold_list = [get_number_from_string(item.string)[0] 
                    for item in all_a_tag[1:]]
            threshold_value = reduce(lambda x, y: x + (1 if y > 0 else 0), 
                    threshold_list, 0)
            if threshold_value < threshold or all_a_tag[0].get("title") == u'[已重置]':
                return False
            return True
                        
        page_num = (num - 1) / 20 + 1 
        follow_soup = self.get_soup(self.get_page(url))
        try:
            follow_tag = follow_soup.find("div", attrs={"class": "zh-general-list clearfix"})
            follow_div = follow_tag.find_all("div", attrs={"class": "zm-list-content-medium"})
            for follow_user in follow_div:
                all_a_tag = follow_user.find_all("a")
                if not check(all_a_tag):
                    continue

                url = all_a_tag[0].get("href")
                yield (url, all_a_tag[0].get("title"))
        except (ValueError, AttributeError, KeyError), e:
            logging.warn(u"无法获取用户关注者和被关注者信息|%s|%s|%s", url, self.url, str(e))
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
                    follow_div = soup.find("div", attrs={"class": "zm-list-content-medium"})
                    all_a_tag = follow_div.find_all("a")
                    if not check(all_a_tag):
                        continue
                    url = all_a_tag[0].get("href")
                    yield (url, all_a_tag[0].get("title"))
        except (AttributeError, ValueError, KeyError), e:
            logging.warn(u"无法获取用户关注者和被关注者信息|%s|%s|%s", post_url, self.url, str(e))
            return

    # 关注话题数
    def get_topics_num(self): 
        ''' Return topic number which user follow.'''
        try:
            url = self.url.replace(ZHI_HU_URL, "") + "/topics"
            topics_num = get_number_from_string( \
                    self.soup.find("a", href=url).strong.string)[0]
        except (AttributeError, ValueError, KeyError), e:
            logging.warn(u"无法获取用户关注话题数|%s|%s", self.url, str(e))
            return None
        return topics_num

    # 关注的话题
    def get_topics(self):
        ''' Return Topic iterable which current user follow.'''
        num = self.get_topics_num()
        if num is None or num <= 0:
            return 
        page_num = (num - 1) / 20 + 1

        post_url = self.url + "/topics"
        topic_soup = self.get_soup(self.get_page(post_url))
        try:
            topic_tag = topic_soup.find("div", 
                    attrs={"id": "zh-profile-topic-list"})
            topic_a = topic_tag.find_all("a", 
                    attrs={"class": "zm-list-avatar-link"})
            for a in topic_a:
                url = ZHI_HU_URL + a.get("href")
                yield topic.Topic(url)
        except (AttributeError, ValueError), e:
            logging.warn(u"无法获取用户关注话题信息|%s|%d|%s|%s", post_url, 0, self.url, unicode(e))
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
                    yield topic.Topic(url)
        except (AttributeError, ValueError, KeyError), e:
            logging.warn(u"无法获取用户关注话题|%s|%d|%s|%s", post_url, offset, self.url, str(e))
            return 

    # 关注的专栏数
    def get_follow_posts_num(self):
        ''' Return follow post number. '''
        try:
            url = self.url.replace(ZHI_HU_URL, "") + "/columns/followed"
            follow_posts_num = get_number_from_string(
                    self.soup.find("a", href=url).strong.string)[0]
        except AttributeError, e:
            return 0
        except (KeyError, ValueError), e:
            logging.warn(u"无法获取用户关注专栏数|%s|%s", self.url, str(e))
            return None
        return follow_posts_num

    # 回答的问题
    def get_answers(self):
        ''' Return Answer of user.'''
        num = self.get_answers_num()
        if num is None or num <= 0:
            return
        page = (num + 19) / 20

        for i in range(1, page + 1):
            try:
                get_url = "%s/answers?page=%d" % (self.url, i)
                soup = self.get_soup(self.get_page(get_url))
                answer_list = soup.find("div", id="zh-profile-answer-list"). \
                        find_all("a", class_="question_link")
                for item in answer_list:
                    url = ZHI_HU_URL + item.get("href")
                    yield answer.Answer(url)
            except (AttributeError, ValueError), e:
                logging.warn(u"无法获取用户回答信息|%s|%s|%s", get_url, self.url, unicode(e))
                return 

    # 提的问题
    def get_asks(self):
        ''' Return Question which current user asked.'''
        num = self.get_asks_num()
        if num is None or num <= 0:
            return
        page = (num + 19) / 20

        for i in range(1, page + 1):
            try:
                get_url = "%s/asks?page=%d" % (self.url, i)
                soup = self.get_soup(self.get_page(get_url))
                ask_list = soup.find("div", id="zh-profile-ask-list"). \
                        find_all("a", class_="question_link")
                for item in ask_list:
                    url = ZHI_HU_URL + item.get("href")
                    yield question.Question(url)
            except (AttributeError, ValueError), e:
                logging.warn(u"无法获取用户所提问题信息|%s|%s|%s", get_url, self.url, unicode(e))
                return 

    # 收藏夹
    def get_collections(self):
        ''' Return Collection which user created.'''
        num = self.get_collections_num()
        if num is None or num <= 0:
            return
        page = (num + 19) / 20

        for i in range(1, page + 1):
            try:
                get_url = "%s/collections?page=%d" % (self.url, i)
                soup = self.get_soup(self.get_page(get_url))
                collection_list = soup.find_all("a", class_="zm-profile-fav-item-title")
                for item in collection_list:
                    url = ZHI_HU_URL + item.get("href")
                    yield collection.Collection(url)
            except (AttributeError, ValueError), e:
                logging.warn(u"无法获取用户收藏夹信息|%s|%s|%s", get_url, self.url, unicode(e))
                return 

class UserBrief(ZhiHuPage):
    ''' Get zhihu user brief information.'''
    def __init__(self, user_id):
        params = {"url_token": user_id}
        params = {"params": json.dumps(params)}
        self.user_id = user_id
        self.url = ZHI_HU_URL + "/node/MemberProfileCardV2"
        try:
            self.soup = BeautifulSoup(self.get_page(self.url, params = params).content)
        except AttributeError, e:
            logging.warn("This is url is error %s|%s", self.url, str(e))

    def get_user_id(self):
        ''' Return the id of user.'''
        return self.user_id

    def get_user_name(self):
        ''' Return the name of user.'''
        try:
            user_name = self.soup.find("span", \
                    class_ = "name").string
        except AttributeError, e:
            logging.warn("Can't get user name|%s|%s", user_id, str(e))
            return None
        return user_name

    def get_followers_num(self):
        ''' Return follower number of user.'''
        try:
            self.followers_num =self.soup.find_all( \
                    "span", class_ = "value")[2].string 
            followers_num = self.deal_num(self.followers_num)
        except (KeyError, AttributeError), e:
            logging.warn("Can't get user's followers num|%s|%s", user_id, str(e))
            return None
        return followers_num



if __name__ == '__main__':
    #user = User("http://www.zhihu.com/people/wang-yi-zhu-39-58") 
    #user = User("http://www.zhihu.com/people/zen-kou/") 
    #user = User("http://www.zhihu.com/people/mo-zhi/") 
    #user = User("http://www.zhihu.com/people/lishuhang/") 
    #user = User("http://www.zhihu.com/people/chengyuan") 
    user = User("http://www.zhihu.com/people/qian-lu-55")
    print user.get_action_num()
    print user.get_topics_num()
    print user.get_follow_posts_num()
    count = 0
    for m_topic in user.get_topics():
        count += 1
        print count
        print m_topic.get_topic_name().encode("utf-8")
    for ans in user.get_answers():
        print ans.get_voter_num()
        q = ans.get_question()
        print q.get_title()
        print '--------'

    for q in user.get_asks():
        print q.get_title()
        print q.get_answers_num()
        print q.get_follower_num() 

    for url, name in user.get_followees():
        print url, name
    for url, name in user.get_followers():
        print url, name
    #print user.get_user_name()
    #    print followee.get_user_name()
    #for follower in user.get_followers(4):
    #    print follower.get_user_name()
    #for coll in user.get_collections():
    #    print coll.get_collection_name()

    ub = UserBrief("zen-kou")
    print ub.get_user_name()
    print ub.get_answers_num()
    print ub.get_posts_num()
    print ub.get_followers_num()

