#!/usr/bin/env python3
#-*- coding:utf8 -*-

import sys
sys.path.insert(0,'../www')

import orm, asyncio

from models import User, Blog, Comment

async def test(loop):
    await orm.create_pool(loop=loop, host='127.0.0.1', port=3306, user='www-data', password='www-data', db='webapp')

    u = User(name='yxs', email='test@example.com', passwd = '123456', image='about:blank')

    await u.save()

loop = asyncio.get_event_loop()
loop.run_until_complete(test(loop))
loop.close()
if loop.is_closed():
    sys.exit(0)
