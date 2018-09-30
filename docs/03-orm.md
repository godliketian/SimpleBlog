* [ORM](https://en.wikipedia.org/wiki/Object-relational_mapping)

对象关系映射（Object Relational Mapping，简称ORM，或O/RM，或O/R mapping），是一种程序技术，用于实现面向对象编程语言里不同类型系统的数据之间的转换。从效果上说，它其实是创建了一个可在编程语言里使用的“虚拟对象数据库”。

问题的核心在于将对象的逻辑表示转换为能够存储在数据库中的原子化形式，同时保留对象的属性及其关系，以便在需要时将它们作为对象重新加载。

实现实体的属性与关系型数据库字段的映射，CRUD可以交由ORM生成的代码方式实现，也就是将实体的变化翻译成SQL脚本之后执行到数据库中去，隐藏了数据访问细节，是“封闭”的通用数据库交互。

* 连接池

连接池是维护的数据库连接的缓存，以便在将来需要对数据库发起请求时可以重用连接。

[aiomysql pool](https://aiomysql.readthedocs.io/en/latest/pool.html)

* 事务和事务提交

* 游标

* 回滚协程

* 主键

* @classmethod