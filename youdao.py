#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author = 'wyx'
@time = 2018/11/13 10:21
@annotation = ''
"""
import json
import os
import random
import sys
from hashlib import md5

from workflow import web, Workflow3

OLD_KEY = [{'key': 2002493135, 'keyfrom': 'whyliam-wf-1'}, {'key': 2002493136, 'keyfrom': 'whyliam-wf-2'},
           {'key': 2002493137, 'keyfrom': 'whyliam-wf-3'}, {'key': 2002493138, 'keyfrom': 'whyliam-wf-4'},
           {'key': 2002493139, 'keyfrom': 'whyliam-wf-5'}, {'key': 2002493140, 'keyfrom': 'whyliam-wf-6'},
           {'key': 2002493141, 'keyfrom': 'whyliam-wf-7'}, {'key': 2002493142, 'keyfrom': 'whyliam-wf-8'},
           {'key': 2002493143, 'keyfrom': 'whyliam-wf-9'}, {'key': 2002493189, 'keyfrom': 'whyliam-wf-10'},
           {'key': 2002493190, 'keyfrom': 'whyliam-wf-11'}]


class YouDao(object):
    def __init__(self, key=None, query=None):
        self.wf = None
        self.query = query
        self.result = None
        self.key = random.choice(key) if key else None

    def get_translate(self):

        def api():
            URL = 'https://openapi.youdao.com/api'
            salt = str(random.randint(1, 65536))
            query = self.query.decode('utf-8')
            params = {
                'q': query.encode('utf-8'),
                'from': 'auto',
                'to': 'auto',
                'appKey': self.key['app_key'],
                'salt': salt,
                'sign': md5(
                    (self.key['app_key'] + query + salt + self.key['secret_key']).encode('utf-8')).hexdigest().upper(),
            }
            return URL, params

        def old_api():
            self.key = random.choice(OLD_KEY)
            URL = 'http://fanyi.youdao.com/openapi.do'
            query = self.query.decode('utf-8')
            params = {
                'q': query.encode('utf-8'),
                'type': 'data',
                'doctype': 'json',
                'version': '1.1',
            }
            params.update(self.key)
            return URL, params

        def build_api():
            key_list = self._json_load(os.getenv('youdao_key_list'))
            app_key = os.getenv('youdao_app_key')
            secret_key = os.getenv('youdao_secret_key')
            if key_list:
                self.key = random.choice(key_list)
            elif app_key and secret_key:
                self.key = {
                    'app_key': app_key,
                    'secret_key': secret_key,
                }
            if self.key:
                return api()
            return old_api()

        URL, params = build_api()
        self.log.info(self.key)
        self.log.info(URL)
        self.log.info(params)

        resp = web.get(URL, params=params, timeout=5)
        if resp.status_code != 200:
            return False, '网络问题'
        result = resp.json()
        if result and int(result['errorCode']) != 0:
            return False, result
        self.result = result
        return True, result

    def is_chinese(self, s):
        """包含中文 当 中文"""
        import re
        return bool(re.search(ur'[\u4e00-\u9fa5]+', self._safe_decode(s)))

    def get_phonetic(self):
        """音标"""
        basic = self.result['basic']
        phonetic = ''
        if self.is_chinese(self.query) and 'phonetic' in basic:
            phonetic += u'[{}]'.format(basic['phonetic'])
        if 'us-phonetic' in basic:
            phonetic += u' [美: {}]'.format(basic['us-phonetic'])
        if 'uk-phonetic' in basic:
            phonetic += u' [英: {}]'.format(basic['uk-phonetic'])
        return phonetic

    def _safe_decode(self, s):
        if s:
            return s if isinstance(s, unicode) else s.decode('utf-8')
        return s

    def _json_load(self, json_str):
        if json_str:
            return json.loads(json_str)
        return None

    def add_item(self, title, subtitle='', arg=None, valid=True, icon=None):
        """

        :param title:
        :param subtitle:
        :param arg:
        :param valid: True 如果设置copy to clipboard 复制 arg 的内容
        :param icon:
        :return:
        """

        if arg is None:
            arg = title

        self.wf.add_item(title=self._safe_decode(title), subtitle=self._safe_decode(subtitle),
                         arg=self._safe_decode(arg), valid=valid, icon=icon, largetext=self._safe_decode(title))

    def build_arg(self, **kwargs):
        arg_dict = {
            'query': self.query,
            'pronounce': kwargs.get('pronounce', ''),
            'copy': kwargs.get('copy', ''),
            'is_chinese': self.is_chinese(kwargs.get('pronounce', ''))
        }
        d = json.dumps(arg_dict, separators=(',', ':'))
        return d

    def send_feedback(self, is_ok, resp):
        if not is_ok:
            self.add_item('翻译出错', '{}'.format(resp), self.build_arg(
                copy='errorCode {} 查看 http://ai.youdao.com/docs/doc-trans-api.s#p06'.format(resp['errorCode'])))
            return
        # 中文查词判断
        is_chinese = self.is_chinese(self.query)

        if 'translation' in resp:
            # 翻译结果
            for title in resp['translation']:
                self.add_item(title,
                              self.query,
                              arg=self.build_arg(
                                  copy=title, pronounce=title if is_chinese else self.query
                              ))

        if 'basic' in resp:
            # 基本词典, 查词时才有
            for e in resp['basic']['explains']:
                self.add_item(e, self.query, arg=self.build_arg(copy=e, pronounce=e))

            # 英文查词才有音标
            if 'phonetic' in resp['basic']:
                phonetic = self.get_phonetic()
                self.add_item(phonetic, 'cmd+Enter发音', arg=self.build_arg(copy=self.query, pronounce=self.query))

        if 'web' in resp:
            # 网络释义
            for w in resp['web']:
                title = ','.join(w['value'])
                self.add_item(title, w['key'],
                              arg=self.build_arg(copy=title, pronounce=title if is_chinese else w['key']))

    def run(self, wf):
        self.query = self.query if self.query is not None else wf.args[0].strip().replace("\\", "")
        self.wf = wf
        self.log = wf.logger
        is_ok, msg = self.get_translate()
        self.send_feedback(is_ok, msg)
        wf.send_feedback()


if __name__ == '__main__':
    wf = Workflow3()
    workflow = YouDao()
    sys.exit(wf.run(workflow.run))
