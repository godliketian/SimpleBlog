#!/usr/bin/env python3
#-*- coding:utf8 -*-

"""
Default configurations.
"""

__author__ = 'yexuesong'

configs = {
    'debug': True,
    'db':{
        'host': '127.0.0.1',
        'port': 3306,
        'user': 'www-data',
        'password': 'www-data',
        'db': 'webapp'
    },
    'session': {
        'secret': 'yxs'
    }
}
