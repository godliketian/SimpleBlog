[python webapp实战](https://www.liaoxuefeng.com/wiki/0014316089557264a6b348958f449949df42a6d3a2e542c000/001432170876125c96f6cc10717484baea0c6da9bee2be4000)

## init env

* CentOS7.5 [Download](https://mirrors.aliyun.com/centos/7/isos/x86_64/CentOS-7-x86_64-Minimal-1804.iso)

* Python3.6.6 and Pip3

    ```
    yum -y install epel-release
    
    yum -y install python36
    
    curl https://bootstrap.pypa.io/get-pip.py | python3.6
    
    python3 get-pip.py
    
    ```

* MySQL8.0

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
