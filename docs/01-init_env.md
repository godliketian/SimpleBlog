## init env

* CentOS7.5

* Install Python3.6.6 and Pip3

    ```
    yum -y install epel-release
    
    yum -y install python36
    
    curl https://bootstrap.pypa.io/get-pip.py | python3.6
    
    python3 get-pip.py
    
    ```

* Install MySQL8.0

    ```
    yum localinstall https://repo.mysql.com//mysql80-community-release-el7-1.noarch.rpm
    
    yum -y install mysql-community-server
    
    systemctl start mysqld.service
    
    systemctl enable mysqld.service
    
    grep 'temporary password' /var/log/mysqld.log    # 获取root账户的临时密码
    
    mysql -u root -p    # 输入临时密码
    
    set global validate_password.policy=0;
    set global validate_password.length=1;    # 关闭强密码策略
    
    ALTER USER 'root'@'localhost' IDENTIFIED BY '123456';    # 将密码改为123456
    ```
