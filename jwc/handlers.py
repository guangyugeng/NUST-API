#!/usr/bin/env python
# encoding: utf-8

from hashlib import md5
import re

import tornado.web
import tornado.httpclient
import requests
from bs4 import BeautifulSoup
import ujson
import json

jwc_domain = 'http://202.119.81.112:9080'


def login_session(username, password):
    data = {
        'method': 'verify',
        'USERNAME': username,
        'PASSWORD': md5(password).hexdigest().upper()
    }
    http = requests.Session()
    res = http.get(jwc_domain + '/njlgdx/xk/LoginToXk', params=data)
    if re.search(u'退出', res.text):
        return http


def parser_table(soup, table):
    res = {}
    for row in table.contents[3::2]:
        ro = []
        term = unicode(row.contents[3].string)
        for col in row.contents[5::2]:
            ro.append(unicode(col.string))
        res.setdefault(term, [])
        res[term].append(ro)
    return res

def parser_classtable(soup, classtable):
    res = {}
    count0 = 0
    week_list = []
    for row in classtable.find_all('tr'):
        count0 += 1
        th = row.find_all('th')
        
        if count0 == 1:
            for week in th:
                for w in week.stripped_strings:
                    res.setdefault(unicode(w), [])
                    week_list.append(w)
            continue
       
        count1 = 0
        for col in row.find_all('td'):
            col = col.find_all(class_ = 'kbcontent1')
            for w in col:
                class_list = []
                count = 0
                u = unicode('')
                for string in w.stripped_strings:
                    count += 1
                    if count in [1,4,7]:
                        u = string
                    if count in [2,5,8]:
                        class_list.append((u, string))
            for th0 in th:
                for th1 in th0.stripped_strings:

                    class0 = (th1, class_list)

            res[week_list[count1]].append(class0)

            count1 += 1
    return res



class StudentInfoHandler(tornado.web.RequestHandler):
    def get(self):
        data = {
            'method': 'verify',
            'USERNAME': self.get_argument("user"),
            'PASSWORD': md5(self.get_argument("pwd")).hexdigest().upper()
        }
        http = requests.Session()
        res = http.get(jwc_domain+'/njlgdx/xk/LoginToXk', params=data)
        if re.search(u'退出', res.text):
            res = http.get(jwc_domain+'/njlgdx/grxx/xsxx')
            res.encoding = 'utf-8'
            patt = r'''
            <table\s*id=\"xjkpTable\".*?>\s*<tr.*?>.*?</tr>\s*<tr.*?>.*?</tr>\s*
            <tr.*?>\s*
            <td.*?>(?P<college>.*?)</td>\s*
            <td.*?>(?P<major>.*?)</td>\s*
            <td.*?>.*?</td>\s*
            <td.*?>(?P<class>.*?)</td>
            .*?</tr>\s*
            <tr.*?>\s*
            <td.*?>.*?</td>\s*
            <td.*?>(?P<name>.*?)</td>
            .*?</tr>\s*
            <tr.*?>.*?</tr>\s*
            <tr.*?>\s*
            <td.*?>.*?</td>\s*
            <td.*?>(?P<subject>.*?)</td>
            .*?</tr>
            '''
            p = re.compile(patt, re.DOTALL | re.MULTILINE | re.VERBOSE)
            result = p.search(res.text)
            self.write((result.group('name')) + '<br/>')
            self.write((result.group('class')) + '<br/>')
            self.write((result.group('college')) + '<br/>')
            self.write((result.group('major')) + '<br/>')
            self.write((result.group('subject')) + '<br/>')


class ScoreHandlers(tornado.web.RequestHandler):
    def get(self):
        user, pwd = map(self.get_argument, ['user', 'pwd'])
        http = login_session(user, pwd)
        score_page = http.get(jwc_domain + '/njlgdx/kscj/cjcx_list')
        soup = BeautifulSoup(score_page.text)
        res = {}
        table = soup.find(id='dataList')
        for row in table.contents[3::2]:
            ro = []
            term = unicode(row.contents[3].string)
            for col in row.contents[5::2]:
                ro.append(unicode(col.string))
            res.setdefault(term, [])
            res[term].append(ro)
        self.write(ujson.dumps(res, sort_keys=True))




class ScoreHandlers_gc0(tornado.web.RequestHandler):
    def get(self):
        user, pwd = map(self.get_argument, ['user', 'pwd'])
        http = login_session(user, pwd)
        score_page = http.get(jwc_domain + '/njlgdx/kscj/cjcx_list')
        soup = BeautifulSoup(score_page.text)
        table = soup.find(id='dataList')
        res = parser_table(soup, table)

        self.write(json.dumps(res))
        """
        self.render('index.html')
        """

class classtableHandlers(tornado.web.RequestHandler):
    def get(self):
        user, pwd = map(self.get_argument, ['user', 'pwd'])
        http = login_session(user, pwd)
        classtable_page = http.get(jwc_domain + '/njlgdx/xskb/xskb_list.do?Ves632DSdyV=NEW_XSD_PYGL')
        soup = BeautifulSoup(classtable_page.text)

        table = soup.find(id='dataList')
        res0 = parser_table(soup, table)
        self.write(json.dumps(res0))        

        classtable = soup.find(id='kbtable')
        res1 = parser_classtable(soup, classtable)
        self.write(json.dumps(res1))
