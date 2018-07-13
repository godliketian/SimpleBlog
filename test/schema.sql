-- schema.sql

drop database if exists webapp;

create database webapp;

use webapp;
/*
grant select, insert, update, delete on webapp.* to 'www-data'@'localhost' identified by 'www-data';
该sql语句在mysql5.0中可用，但是在8.0中已经不可用了。需要先创建用户，再授权，不能在一条sql语句中操作，新写法如下。
官网说明: https://dev.mysql.com/doc/refman/8.0/en/adding-users.html
*/
create user 'www-data'@'localhost' identified by 'www-data';
grant select, insert, update, delete on webapp.* to 'www-data'@'localhost' with grant option;

create table users (
	    `id` varchar(50) not null,
	    `email` varchar(50) not null,
	    `passwd` varchar(50) not null,
	    `admin` bool not null,
	    `name` varchar(50) not null,
	    `image` varchar(500) not null,
	    `created_at` real not null,
	    unique key `idx_email` (`email`),
	    key `idx_created_at` (`created_at`),
	    primary key (`id`)
) engine=innodb default charset=utf8;

create table blogs (
	    `id` varchar(50) not null,
	    `user_id` varchar(50) not null,
	    `user_name` varchar(50) not null,
	    `user_image` varchar(500) not null,
	    `name` varchar(50) not null,
	    `summary` varchar(200) not null,
	    `content` mediumtext not null,
	    `created_at` real not null,
	    key `idx_created_at` (`created_at`),
	    primary key (`id`)
) engine=innodb default charset=utf8;

create table comments (
	    `id` varchar(50) not null,
	    `blog_id` varchar(50) not null,
	    `user_id` varchar(50) not null,
	    `user_name` varchar(50) not null,
	    `user_image` varchar(500) not null,
	    `content` mediumtext not null,
	    `created_at` real not null,
	    key `idx_created_at` (`created_at`),
	    primary key (`id`)
) engine=innodb default charset=utf8;
