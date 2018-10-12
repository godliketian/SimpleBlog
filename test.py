#!/usr/bin/env python3
#-*- coding:utf8 -*-

__author__ = 'XueSong.Ye'

import os

print('Process (%s) start...' % os.getpid())

pid = os.fork()
if pid == 0:
    print('I am child process(%s) and my parentis %s.' % (os.getpid(), os.getppid()))
else:
    print('I (%s) just created a child process (%s).' % (os.getpid(), pid))
