#!/usr/bin/env python
# -*- coding: utf-8 -*-

from zhihu.network import Login
t = Login()
t.login(email="1054059790@qq.com", passwd="xiao105405")

from zhihu import answer
from zhihu import topic
from zhihu import question
from zhihu import user
from zhihu import collection
from zhihu import setting

def test_answer():
    my_answer = answer.Answer("https://www.zhihu.com/question/30909334/answer/50176562")
    print "所属问题:", my_answer.get_question().get_title()
    print "作者:", my_answer.get_auther().get_user_name()
    print "赞同数:", my_answer.get_voter_num()
    try:
        voters = my_answer.get_voters().next()
        print "其中一个赞同者:", voters[0], voters[1]
    except StopIteration, e:
        pass
    print "回答时间:", my_answer.get_answer_time()
    print "属于的话题:"
    for tp in my_answer.get_topics_name_and_url():
        print tp[0], tp[1]
    print "回答内容:", my_answer.get_content()


def test_topic():
    my_topic = topic.Topic("https://www.zhihu.com/topic/19570098")
    print "话题名:", my_topic.get_topic_name()
    print "话题问题页数:", my_topic.get_topic_page_num()
    print "话题下的关注数:", my_topic.get_topic_follower_num()
    print "其中一个问题:"
    try:
        my_question = my_topic.get_questions().next()
        print my_question.get_title()
        print my_question.get_detail()
        print my_question.get_answers_num()
        print my_question.get_follower_num()
        for tp in my_question.get_topics():
            print tp.get_topic_name()
    except StopIteration, e:
        pass
    
    
    print '话题树的一个节点:'
    my_topic_node = topic.TopicNode("http://www.zhihu.com/topic/19612637/organize/entire")
    print "节点名字:", my_topic_node.get_node_name()
    print "节点URL:", my_topic_node.get_node_url()
    print "话题ID:", my_topic_node.get_topic_id()
    print "话题URL:", my_topic_node.get_topic_url()
    print "话题问题页数:", my_topic_node.get_topic().get_topic_page_num()
    print "子节点:"
    childs = my_topic_node.get_children_nodes()
    for child in childs:
        if not isinstance(child, basestring):
            print child.get_node_name()

def test_question():
    url = u'http://www.zhihu.com/question/22808635'
    problem = question.Question(url)
    print "问题题目:", problem.get_title()
    print "问题详细描述:", problem.get_detail()
    print "问题回答个数:", problem.get_answers_num()
    print "问题关注数量:", problem.get_follower_num()
    print "问题所属话题:"
    topics = problem.get_topics()
    for my_topic in topics:
        print my_topic.get_topic_name()
    print '回答作者:'
    count = 0
    for ans in problem.get_answers():
        count +=1
        print '------', count
        auther = ans.get_auther()
        if auther:
            print auther.get_user_name()

def test_user():
    my_user = user.User("https://www.zhihu.com/people/qian-lu-55")
    print '用户名:', my_user.get_user_name()
    print '用户Id:', my_user.get_user_id()
    print '赞同数:', my_user.get_upvote_num()
    print '感谢数:', my_user.get_thanks_num()

    count = 0
    print '关注了:', my_user.get_followees_num()
    for u in my_user.get_followees():
        print u
        count += 1
        if count > 2: break
    print '关注者数:', my_user.get_followers_num() 
    count = 0
    for u in my_user.get_followers():
        print u
        count += 1
        if count > 2: break

    print '关注话题数:', my_user.get_topics_num()
    count = 0
    for t in my_user.get_topics():
        print t
        count += 1
        if count > 2: break
    print '关注专栏数:', my_user.get_follow_posts_num()

    print '提问数，回答数, 专利文章数, 收藏夹数, 公共编辑数:', my_user.get_action_num()
    print '回答:'
    count = 0
    for ans in my_user.get_answers():
        print ans
        count += 1
        if count > 2: break
    print '提问:'
    count = 0
    for q in my_user.get_asks():
        print q
        count += 1
        if count > 2: break

    ub = user.UserBrief("zen-kou")
    print ub.get_user_name()
    #print ub.get_answers_num()
    #print ub.get_posts_num()
    print ub.get_followers_num()

def test_collecton():
    #my_collection = collection.Collection("https://www.zhihu.com/collection/30792398")
    my_collection = collection.Collection("https://www.zhihu.com/collection/19764022")
    print '收藏夹名称: ', my_collection.get_collection_name()
    print '收藏夹id: ',  my_collection.get_collection_id()
    print '收藏夹URL: ', my_collection.get_collection_url()
    print '收藏夹创建者: ', my_collection.get_creator().get_user_name()
    
    print '收藏夹回答数: ', my_collection.get_answers_num()
    print '收藏夹的回答: '
    answers = my_collection.get_answers()
    count = 0
    for ans in answers:
        print ans.get_answer_id()
        count += 1
        if count > 5: break
    print '收藏夹的关注数量: ', my_collection.get_followers_num()
    print '收藏夹关注者: '
    count = 0
    users = my_collection.get_followers()
    for ur in users:
        print ur.get_user_name()
        count += 1
        if count > 5: break
        




if __name__ == '__main__':
    print '--------Test User & UserBrief -----'
    test_user()
    print '--------Test Answer--------'
    test_answer()
    print '------- Test Topic -------'
    test_topic()
    print '------ Test Question ------'
    test_question()
    print '------ Test Collection------'
    test_collecton()

