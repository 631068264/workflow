#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author = 'wyx'
@time = 2018/11/13 10:21
@annotation = ''
"""
import argparse
import json
import sys

from workflow import Workflow3

reload(sys)
sys.setdefaultencoding('utf8')


def shell(cmd):
    import subprocess
    return subprocess.check_output(cmd, shell=True)


def main(wf):
    parser = argparse.ArgumentParser()
    parser.add_argument('query')
    parser.add_argument('action')
    parser.add_argument('--actor', help='chinese actor')
    arg = parser.parse_args(wf.args)

    query = arg.query
    arg_dict = json.loads(query)
    action = arg.action
    actor = arg.actor

    if action in ['copy', 'query']:
        sys.stdout.write(arg_dict.get(action).strip())

    elif action == 'pronounce':
        pronounce = arg_dict[action]
        is_chinese = arg_dict['is_chinese']
        if is_chinese:
            cmd = 'say "{}" -v {}'.format(pronounce, actor if actor else 'Ting-Ting')
            shell(cmd)
        else:
            cmd = 'say "{}" -v {}'.format(pronounce, 'Samantha')
            shell(cmd)


if __name__ == '__main__':
    wf = Workflow3()
    sys.exit(wf.run(main))
