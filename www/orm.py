#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'XueSong.Ye'

"""ORM MEANS OBJECT-RELATIONAL MAPPING

async 替换了 @asyncio.coroutine; await 替换了yield from; 这是Python3.5的新语法，可以让coroutine的代码更加简洁

ORM框架的目的是将数据库表的每条记录映射为对象，每条记录的字段和对象的属性相应，同时透过对象方法执行SQL命令。

3. __pool.get() 替换了 yield from __pool
"""

import asyncio, logging

import aiomysql


def log(sql, args=()):
    logging.info('SQL: %s' % sql)

# Close pool
pass

# Create connect pool
# Parameter: host, port, user, password, db, charset, autocommit, maxsize, minsize, loop
async def create_pool(loop, **kw):
    logging.info('  create database connection pool...')
    global __pool
    __pool = await aiomysql.create_pool(
        host=kw.get('host', 'localhost'),
        port=kw.get('port', 3306),
        user=kw['user'],
        password=kw['password'],
        db=kw['db'],
        charset=kw.get('charset', 'utf8'),
        autocommit=kw.get('autocommit', True),
        maxsize=kw.get('maxsize', 10),
        minsize=kw.get('minsize', 1),
        loop=loop
    )

# Package SELECT function that can execute SELECT command.
# Setup 1:acquire connection from connection pool.
# Setup 2:create a cursor to execute MySQL command.
# Setup 3:execute MySQL command with cursor.
# Setup 4:return query result.
async def select(sql, args, size=None):
    log(sql, args)
    global __pool
    async with __pool.get() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:

            await cur.execute(sql.replace('?', '%s'), args or ())
            if size:
                rs = await cur.fetchmany(size)
            else:
                rs = await cur.fetchall()
        logging.info('rows returned: %s' % len(rs))
        return rs

# Package execute function that can execute INSERT,UPDATE and DELETE command. 定义通用的execute()函数来执行增删改。

async def execute(sql, args, autocommit=True):
    log(sql)
    # acqiure connection from connection pool
    async with __pool.get() as conn:
        # 如果MySQL禁止隐式提交，则标记事务开始
        if not autocommit:
            await conn.begin()
        try:
            # create cursor to execute MySQL command
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(sql.replace('?', '%s'), args)
                affected = cur.rowcount
            # 如果MySQL禁止隐式提交，手动提交事务
            if not autocommit:
                await conn.commit()
        # 如果事务提交错误，则退回
        except BaseException as e:
            if not autocommit:
                await conn.rollback()
            raise
        # return number of affected rows.
        return affected

# Create placeholder with '?'
def create_args_string(num):
    L = []
    for n in range(num):
        L.append('?')
    return ', '.join(L)

# A base class about Field
# 描述 字段的字段名，数据类型，键信息，默认值
class Field(object):

    def __init__(self, name, column_type, primary_key, default):
        self.name = name
        self.column_type = column_type
        self.primary_key = primary_key
        self.default = default

    def __str__(self):
        return '<%s, %s:%s>' % (self.__class__.__name__, self.column_type, self.name)


class StringField(Field):

    def __init__(self, name=None, primary_key=False, default=None, ddl='varchar(100)'):
        super().__init__(name, ddl, primary_key, default)


class BooleanField(Field):

    def __init__(self, name=None, default=False):
        super().__init__(name, 'boolean', False, default)


class IntegerField(Field):

    def __init__(self, name=None, primary_key=False, default=0):
        super().__init__(name, 'bigint', primary_key, default)


class FloatField(Field):

    def __init__(self, name=None, primary_key=False, default=0.0):
        super().__init__(name, 'real', primary_key, default)


class TextField(Field):

    def __init__(self, name=None, default=None):
        super().__init__(name, 'text', False, default)

# Meatclass about ORM
# 首先，拦截类的创建；然后，修改类；最后，返回修改后的类。
class ModelMetaclass(type):
    # 采集应用元类的子类属性信息
    # 将采集的信息作为参数传入 __new__ 方法
    # 应用 __new__ 方法修改类
    def __new__(cls, name, bases, attrs):
        # 排除Model类本身，即不对Model类应用元类
        if name=='Model':
            return type.__new__(cls, name, bases, attrs)
        # 获取table名称，若 __table__为None， 则取用类名
        tableName = attrs.get('__table__', None) or name
        logging.info('  found model: %s (table: %s)' % (name, tableName))
        # 获取所有的Field和主键名，存储映射表的属性（键-值）
        mappings = dict()
        # 存储映射表类的非主键属性（仅键）
        fields = []
        # 主键对应字段
        primaryKey = None
        for k, v in attrs.items():
            if isinstance(v, Field):
                logging.info('  found mapping: %s ==> %s' % (k, v))
                mappings[k] = v
                if v.primary_key:
                    # 找到主键
                    logging.info('  found primary key %s' % k)
                    if primaryKey:
                        raise StandardError('Duplicate primary key for field: %s' % k)
                    primaryKey = k
                else:
                    fields.append(k)
        # 如果没有主键，抛出异常
        if not primaryKey:
            raise StandardError('Primary key not found.')
        # 删除映射表类的属性，以便应用新的属性
        for k in mappings.keys():
            attrs.pop(k)
        # 使用反单引号" ` "区别MySQL保留关键字，提高兼容性
        escaped_fields = list(map(lambda f: '`%s`' % f, fields))
        # 重写属性
        attrs['__mappings__'] = mappings # 保存属性和列的映射关系
        attrs['__table__'] = tableName
        attrs['__primary_key__'] = primaryKey # 主键属性名
        attrs['__fields__'] = fields # 除主键外的属性名
        # 构造默认的SELECT, INSERT, UPDATE和DELETE语句
        attrs['__select__'] = 'select `%s`, %s from `%s`' % (primaryKey, ', '.join(escaped_fields), tableName)
        attrs['__insert__'] = 'insert into `%s` (%s, `%s`) values (%s)' % (
            tableName, ', '.join(escaped_fields), primaryKey, create_args_string(len(escaped_fields) + 1))
        attrs['__update__'] = 'update `%s` set %s where `%s`=?' % (
            tableName, ', '.join(map(lambda f: '`%s`=?' % (mappings.get(f).name or f), fields)), primaryKey)
        attrs['__delete__'] = 'delete from `%s` where `%s`=?' % (tableName, primaryKey)
        # 返回修改后的类
        return type.__new__(cls, name, bases, attrs)


# A base class about Model
# 继承dict类特性
# 附加方法：以属性形式获取值，拦截私设属性
class Model(dict, metaclass=ModelMetaclass):

    def __init__(self, **kw):
        super(Model, self).__init__(**kw)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Model' object has no attribute '%s'" % key)

    def __setattr__(self, key, value):
        self[key] = value

    def getValue(self, key):
        return getattr(self, key, None)

    def getValueOrDefault(self, key):
        value = getattr(self, key, None)
        if value is None:
            field = self.__mappings__[key]
            if field.default is not None:
                value = field.default() if callable(field.default) else field.default
                logging.debug('using default value for %s: %s' % (key, str(value)))
                setattr(self, key, value)
        return value

    # ORM框架下，每条记录作为对象返回
    # @classmethod定义类方法，类对象cls便完成某些操作
    @classmethod
    async def findAll(cls, where=None, args=None, **kw):
        ' find objects by where clause. '
        sql = [cls.__select__]
        # 添加WHERE子句
        if where:
            sql.append('where')
            sql.append(where)
        if args is None:
            args = []
        orderBy = kw.get('orderBy', None)
        # 添加ORDER BY子句
        if orderBy:
            sql.append('order by')
            sql.append(orderBy)
        limit = kw.get('limit', None)
        # 添加LIMIT子句
        if limit is not None:
            sql.append('limit')
            if isinstance(limit, int):
                sql.append('?')
                args.append(limit)
            elif isinstance(limit, tuple) and len(limit) == 2:
                sql.append('?, ?')
                args.extend(limit)
            else:
                raise ValueError('Invalid limit value: %s' % str(limit))
        # execute SQL
        rs = await select(' '.join(sql), args)
        # 将每条记录作为对象返回
        return [cls(**r) for r in rs]

    # 过滤结果数量
    @classmethod
    async def findNumber(cls, selectField, where=None, args=None):
        ' find number by select and where. '
        sql = ['select %s _num_ from `%s`' % (selectField, cls.__table__)]
        # 添加WHERE子句
        if where:
            sql.append('where')
            sql.append(where)
        rs = await select(' '.join(sql), args, 1)
        if len(rs) == 0:
            return None
        return rs[0]['_num_']
    
    # 返回主键的一条记录
    @classmethod
    async def find(cls, pk):
        ' find object by primary key. '
        rs = await select('%s where `%s`=?' % (cls.__select__, cls.__primary_key__), [pk], 1)
        if len(rs) == 0:
            return None
        return cls(**rs[0])

    # INSERT command
    async def save(self):
        args = list(map(self.getValueOrDefault, self.__fields__))
        args.append(self.getValueOrDefault(self.__primary_key__))
        rows = await execute(self.__insert__, args)
        if rows != 1:
            logging.warn('failed to insert record: affected rows: %s' % rows)

    # UPDATE command
    async def update(self):
        args = list(map(self.getValue, self.__fields__))
        args.append(self.getValue(self.__primary_key__))
        rows = await execute(self.__update__, args)
        if rows != 1:
            logging.warn('failed to update by primary key: affected rows: %s' % rows)

    # DELETE command
    async def remove(self):
        args = [self.getValue(self.__primary_key__)]
        rows = await execute(self.__delete__, args)
        if rows != 1:
            logging.warn('failed to remove by primary key: affected rows: %s' % rows)
