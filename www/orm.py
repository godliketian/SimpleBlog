#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'XueSong.Ye'

"""ORM means Object Relational Mapping

async 替换了 @asyncio.coroutine; await 替换了yield from; 这是Python3.5的新语法，可以让coroutine的代码更加简洁

ORM框架的目的是将数据库表的每条记录映射为对象，每条记录的字段和对象的属性相应，同时透过对象方法执行SQL命令。

__pool.get() 替换了 yield from __pool
"""

import asyncio, logging

import aiomysql


def log(sql, args=()):
    logging.info('SQL: %s' % sql)


async def create_pool(loop, **kw):
    """创建全局连接池，**kw 关键字参数集，用于传递 host port user password db 等的数据库连接参数。"""
    logging.info('  create database connection pool...')
    global __pool  # 将 __pool 定义为全局变量
    __pool = await aiomysql.create_pool(
        host=kw.get('host', 'localhost'),
        port=kw.get('port', 3306),
        user=kw['user'],
        password=kw['password'],
        db=kw['db'],
        charset=kw.get('charset', 'utf8'),
        autocommit=kw.get('autocommit', True),  # 设置自动提交事务，默认打开。
        maxsize=kw.get('maxsize', 10),
        minsize=kw.get('minsize', 1),
        loop=loop  # 需要传递一个事件循环实例，若无特别声明，默认使用asyncio.get_event_loop()
    )


async def select(sql, args, size=None):
    """实现SQL语句：SELECT。
    
    传入参数为：SQL语句，SQL语句中占位符对应的参数集，返回记录行数。
    执行为：从连接池获取连接->创建游标用来执行MySQL命令->用游标执行MySQL命令->返回查询结果。
    """
    log(sql, args)
    global __pool
    async with __pool.get() as conn:  # 从连接池中获取一个连接，使用完后自动释放。
        async with conn.cursor(aiomysql.DictCursor) as cur:  # 创建一个游标，返回由dict组成的list，使用完后自动释放。
            await cur.execute(sql.replace('?', '%s'),
                              args or ())  # 执行SQL，mysql的占位符是%s，和python一样，为了coding的便利，先用SQL的占位符？写SQL语句，最后执行时在转换过来。
            if size:
                rs = await cur.fetchmany(size)
            else:
                rs = await cur.fetchall()
        logging.info('rows returned: %s' % len(rs))
        return rs


async def execute(sql, args, autocommit=True):
    """实现SQL语句：INSERT、UPDATE、DELETE。

    传入参数分别为：SQL语句、SQL语句中占位符对应的参数集、默认打开MySQL的自动提交事务。
    定义通用的execute()函数来执行增删改。
    """
    log(sql)
    async with __pool.get() as conn:
        if not autocommit:  # 如果MySQL禁止隐式提交，则标记事务开始。
            await conn.begin()
        try:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(sql.replace('?', '%s'), args)
                affected = cur.rowcount  # 获得影响的行数
            if not autocommit:  # 如果MySQL禁止隐式提交，手动提交事务
                await conn.commit()
        except BaseException as e:  # 如果事务提交错误，则退回
            if not autocommit:
                await conn.rollback()  # 回滚当前启动的协程
            raise
        return affected  # return number of affected rows.


def create_args_string(num):
    """按照参数个数制作占位符字符串，用于生成SQL语句"""
    L = []
    for n in range(num):  # SQL的占位符是?, num是多少就插入多少个占位符
        L.append('?')
    return ', '.join(L)  # 将L拼接成字符串返回, 例如num=3时，返回"?, ?, ?"


class Field(object):
    """定义一个数据类型的基类。

    用于衍生各种在ORM中对应数据库的数据类型的类。
    描述字段的字段名，数据类型，键信息，默认值。
    """

    def __init__(self, name, column_type, primary_key, default):
        """传入参数对应列名，数据类型，主键，默认值。"""
        self.name = name
        self.column_type = column_type
        self.primary_key = primary_key
        self.default = default

    def __str__(self):
        """print(Field_object)时，返回类名Field，数据类型，列名。"""
        return '<%s, %s:%s>' % (self.__class__.__name__, self.column_type, self.name)


class StringField(Field):
    """从Field继承，定义一个字符类，在ORM中对应数据库对的字符类型，默认可变长字符串长度等于100."""

    def __init__(self, name=None, primary_key=False, default=None, ddl='varchar(100)'):
        super().__init__(name, ddl, primary_key, default)


class BooleanField(Field):
    """定义一个布尔类"""

    def __init__(self, name=None, default=False):
        super().__init__(name, 'boolean', False, default)


class IntegerField(Field):
    """定义一个整数类，在ORM中对应数据库的BIGINT整数类型"""

    def __init__(self, name=None, primary_key=False, default=0):
        super().__init__(name, 'bigint', primary_key, default)


class FloatField(Field):
    """定义一个浮点数类，在ORM中对应数据库的REAL双精度浮点数类型"""

    def __init__(self, name=None, primary_key=False, default=0.0):
        super().__init__(name, 'real', primary_key, default)


class TextField(Field):
    """定义一个文本类，在ORM中对应数据库的TEXT长文本数类型"""

    def __init__(self, name=None, default=None):
        super().__init__(name, 'text', False, default)


class ModelMetaclass(type):
    """定义一个元类，定制类与数据库的各种映射关系，让继承这个元类的类实现ORM。

    首先，拦截类的创建；然后，修改类；最后，返回修改后的类。
    """

    def __new__(cls, name, bases, attrs):
        """用metaclass=ModelMetaclass创建类时，通过这个方法生成类。

        采集应用元类的子类属性信息，将采集的信息作为参数传入 __new__ 方法，应用 __new__ 方法修改类。
        """
        if name == 'Model':  # 排除Model类本身，即不对Model类应用元类
            return type.__new__(cls, name, bases, attrs)  # 当前准备创建的类的对象、类的名字model、类继承的父类集合、类的方法集合
        tableName = attrs.get('__table__', None) or name  # 获取table名称，默认为None，或者为类名
        logging.info('  found model: %s (table: %s)' % (name, tableName))
        mappings = dict()  # 获取所有的Field和主键名，存储映射表的属性（键-值），列名和对应的数据类型
        fields = []  # 存储映射表类的非主键属性（仅键），非主键的列
        primaryKey = None  # 主键对应字段，用于主键查重，默认为None
        for k, v in attrs.items():  # 遍历attrs方法集合
            if isinstance(v, Field):  # 提取数据类的列
                logging.info('  found mapping: %s ==> %s' % (k, v))
                mappings[k] = v  # 存储列名和数据类型
                if v.primary_key:  # 找到主键
                    if primaryKey:  # 查找主键和查重，有重复则抛出异常
                        raise StandardError('Duplicate primary key for field: %s' % k)
                    primaryKey = k
                else:
                    fields.append(k)  # 存储非主键的列名
        if not primaryKey:  # 整个表如果没有主键，抛出异常
            raise StandardError('Primary key not found.')
        for k in mappings.keys():
            attrs.pop(k)  # 过滤掉列，只剩下方法；删除映射表类的属性，以便应用新的属性
        escaped_fields = list(map(lambda f: '`%s`' % f, fields))  # 使用反单引号" ` "区别MySQL保留关键字，提高兼容性；``(可执行命令)区别于''(字符串标识)
        # 重写属性
        attrs['__mappings__'] = mappings  # 保存属性和列的映射关系
        attrs['__table__'] = tableName
        attrs['__primary_key__'] = primaryKey  # 主键属性名
        attrs['__fields__'] = fields  # 除主键外的属性名
        # 构造默认的SELECT, INSERT, UPDATE和DELETE语句
        attrs['__select__'] = 'select `%s`, %s from `%s`' % (
            primaryKey, ', '.join(escaped_fields), tableName)  # 构造select执行语句，查整个表
        attrs['__insert__'] = 'insert into `%s` (%s, `%s`) values (%s)' % (
            tableName, ', '.join(escaped_fields), primaryKey,
            create_args_string(len(escaped_fields) + 1))  # 构造insert执行语句，？作为占位符
        attrs['__update__'] = 'update `%s` set %s where `%s`=?' % (
            tableName, ', '.join(map(lambda f: '`%s`=?' % (mappings.get(f).name or f), fields)),
            primaryKey)  # 构造update执行语句，根据主键值更新对应一行的记录，？作为占位符，待传入更新值和主键值
        attrs['__delete__'] = 'delete from `%s` where `%s`=?' % (tableName, primaryKey)  # 构建delete执行语句，根据主键值删除对应行
        return type.__new__(cls, name, bases, attrs)  # 返回当前准备创建的类的对象、类的名字、类继承的父类集合、类的方法集合（经过以上代码处理过的总集合）


class Model(dict, metaclass=ModelMetaclass):
    """定义一个对应数据库数据类型的模板类。通过继承，获得dict的特性和元类的类与数据库的映射关系

    附加方法：以属性形式获取值，拦截私设属性
    由模板类衍生其他类时，这个模板类没有重新定义__new__()方法，因此会使用父类ModelMetaclass的__new__()来生成衍生类，从而实现ORM
    """

    def __init__(self, **kw):
        super(Model, self).__init__(**kw)

    def __getattr__(self, key):
        """ getattr,setattr实现属性动态绑定和获取"""
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Model' object has no attribute '%s'" % key)

    def __setattr__(self, key, value):
        self[key] = value

    def getValue(self, key):
        """返回属性值，默认为None"""
        return getattr(self, key, None)

    def getValueOrDefault(self, key):
        """返回属性值，空则返回默认值"""
        value = getattr(self, key, None)
        if value is None:
            field = self.__mappings__[key]  # 查取属性对应的列的数量类型默认值
            if field.default is not None:
                value = field.default() if callable(field.default) else field.default
                logging.debug('using default value for %s: %s' % (key, str(value)))
                setattr(self, key, value)
        return value

    @classmethod  # ORM框架下，每条记录作为对象返回;@classmethod定义类方法，类对象cls便完成某些操作;添加类方法，对应查表，默认查整个表，可通过where limit设置查找条件。
    async def findAll(cls, where=None, args=None, **kw):
        """find objects by where clause. """
        sql = [cls.__select__]  # 用一个列表存储SELECT语句
        if where:  # 添加WHERE子句作为条件
            sql.append('where')
            sql.append(where)
        if args is None:
            args = []
        orderBy = kw.get('orderBy', None)  # 对查询结果排序排序
        if orderBy:  # 添加ORDER BY子句
            sql.append('order by')
            sql.append(orderBy)
        limit = kw.get('limit', None)  # 截取查询结果
        if limit is not None:  # 添加LIMIT子句
            sql.append('limit')
            if isinstance(limit, int):  # 截取前limit条结果
                sql.append('?')
                args.append(limit)
            elif isinstance(limit, tuple) and len(limit) == 2:  # 略过前limit[0]条记录，开始截取limit[1]条记录
                sql.append('?, ?')
                args.extend(limit)  # 将limit合并到args列表的末尾
            else:
                raise ValueError('Invalid limit value: %s' % str(limit))
        rs = await select(' '.join(sql), args)  # 构造更新后的select语句，并执行，返回属性值[{},{},{}]
        return [cls(**r) for r in rs]  # 将每条记录作为对象返回，返回一个列表。每个元素都是一个dict，相当于一行记录

    @classmethod  # 添加类方法，查找特定列，可通过where设置条件
    async def findNumber(cls, selectField, where=None, args=None):
        ' find number by select and where. '
        sql = ['select %s _num_ from `%s`' % (selectField, cls.__table__)]  # _num_是SQL的一个字段别名用法，Alias关键字可以省略
        # 添加WHERE子句
        if where:
            sql.append('where')
            sql.append(where)
        rs = await select(' '.join(sql), args, 1)  # 更新select语句并执行，返回由dict组成的list
        if len(rs) == 0:
            return None
        return rs[0]['_num_']  # 根据别名key取值

    @classmethod  # 类方法，根据主键查询一条记录并返回
    async def find(cls, pk):
        ' find object by primary key. '
        rs = await select('%s where `%s`=?' % (cls.__select__, cls.__primary_key__), [pk], 1)
        if len(rs) == 0:
            return None
        return cls(**rs[0])  # 将dict作为关键字参数传入当前类的对象

    async def save(self):
        """实例方法，映射插入记录"""
        args = list(map(self.getValueOrDefault, self.__fields__))  # 非主键的值列表
        args.append(self.getValueOrDefault(self.__primary_key__))  # 添加主键值
        rows = await execute(self.__insert__, args)  # 执行insert语句
        if rows != 1:
            logging.warn('failed to insert record: affected rows: %s' % rows)

    async def update(self):
        """映射更新记录"""
        args = list(map(self.getValue, self.__fields__))
        args.append(self.getValue(self.__primary_key__))
        rows = await execute(self.__update__, args)
        if rows != 1:
            logging.warn('failed to update by primary key: affected rows: %s' % rows)

    async def remove(self):
        """映射根据主键值的删除记录"""
        args = [self.getValue(self.__primary_key__)]
        rows = await execute(self.__delete__, args)
        if rows != 1:
            logging.warn('failed to remove by primary key: affected rows: %s' % rows)
