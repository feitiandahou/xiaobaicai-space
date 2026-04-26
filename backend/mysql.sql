DROP DATABASE IF EXISTS `xiaobaicai`;
CREATE DATABASE `xiaobaicai` 
DEFAULT CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;
USE `xiaobaicai`;
-- 1.用户表
DROP TABLE IF EXISTS `users`;

CREATE TABLE `users` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `username` VARCHAR(50) NOT NULL COMMENT '用户名',
  `password` VARCHAR(255) NOT NULL COMMENT '密码哈希',
  `email` VARCHAR(100) DEFAULT NULL COMMENT '邮箱地址',
  `avatar` VARCHAR(255) DEFAULT NULL COMMENT '头像URL',
  `bio` TEXT DEFAULT NULL COMMENT '个人简介',
  `role` VARCHAR(20) NOT NULL DEFAULT 'user' COMMENT '用户角色',
  `is_active` TINYINT(1) UNSIGNED NOT NULL DEFAULT 1 COMMENT '是否启用: 0-禁用, 1-启用',
  `social_links` JSON COMMENT '社交链接(JSON)',
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  
  -- 主键约束
  PRIMARY KEY (`id`),
  
  -- 唯一索引：防止用户名或邮箱重复注册
  UNIQUE KEY `uk_username` (`username`),
  UNIQUE KEY `uk_email` (`email`)
  
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户信息表';
-- 2.文章表
DROP TABLE IF EXISTS `posts`;

CREATE TABLE `posts` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `user_id` BIGINT UNSIGNED NOT NULL COMMENT '作者ID (关联 users.id)',
  `category_id` BIGINT UNSIGNED DEFAULT NULL COMMENT '分类ID',
  `title` VARCHAR(200) NOT NULL COMMENT '文章标题',
  `slug` VARCHAR(200) DEFAULT NULL COMMENT 'URL友好的标识符',
  `summary` VARCHAR(500) DEFAULT NULL COMMENT '文章摘要/简介',
  `content` MEDIUMTEXT NOT NULL COMMENT '文章正文内容',
  `cover_image` VARCHAR(255) DEFAULT NULL COMMENT '封面图URL',
  `status` TINYINT(1) UNSIGNED DEFAULT 0 COMMENT '状态: 0-草稿, 1-已发布, 2-已归档',
  `is_delete` TINYINT(1) UNSIGNED DEFAULT 0 COMMENT '是否删除: 0-否, 1-是 (逻辑删除)',
  `is_top` TINYINT(1) UNSIGNED DEFAULT 0 COMMENT '是否置顶: 0-否, 1-是',
  `view_count` INT UNSIGNED DEFAULT 0 COMMENT '阅读次数',
  `like_count` INT UNSIGNED DEFAULT 0 COMMENT '点赞数',
  `published_at` TIMESTAMP NULL DEFAULT NULL COMMENT '发布时间',
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

  -- 主键约束
  PRIMARY KEY (`id`),
  
  -- 索引设计
  UNIQUE KEY `uk_slug` (`slug`),          -- 唯一索引：用于生成固定的文章链接
  KEY `idx_user_id` (`user_id`),          -- 普通索引：加速查询某用户的所有文章
  KEY `idx_category_id` (`category_id`),  -- 普通索引：加速查询某分类的所有文章
  KEY `idx_status_delete` (`status`, `is_delete`), -- 联合索引：最常用的查询组合
  KEY `idx_published_at` (`published_at`), -- 普通索引：加速按时间排序
  CONSTRAINT `fk_post_user`
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`)
  
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文章表';

-- 3.标签表
DROP TABLE IF EXISTS `tags`;

CREATE TABLE `tags` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '标签ID',
  `name` VARCHAR(50) NOT NULL COMMENT '标签名称',
  `slug` VARCHAR(50) NOT NULL COMMENT '标签URL标识',
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_name` (`name`),
  UNIQUE KEY `uk_slug` (`slug`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='标签表';
-- 4. 创建文章-标签关联表 (post_tags)
DROP TABLE IF EXISTS `post_tags`;

CREATE TABLE `post_tags` (
  `post_id` BIGINT UNSIGNED NOT NULL COMMENT '文章ID',
  `tag_id` BIGINT UNSIGNED NOT NULL COMMENT '标签ID',
  
  PRIMARY KEY (`post_id`, `tag_id`), -- 联合主键，防止重复关联
  KEY `idx_tag_id` (`tag_id`),
  CONSTRAINT `fk_post_tags_post`
    FOREIGN KEY (`post_id`) REFERENCES `posts`(`id`)
    ON DELETE CASCADE,
  CONSTRAINT `fk_post_tags_tag`
    FOREIGN KEY (`tag_id`) REFERENCES `tags`(`id`)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文章标签关联表';
-- 5. 分类表
DROP TABLE IF EXISTS `categories`;

CREATE TABLE `categories` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `name` VARCHAR(50) NOT NULL COMMENT '分类名称',
  `slug` VARCHAR(50) NOT NULL COMMENT 'URL标识符',
  `description` VARCHAR(255) DEFAULT NULL COMMENT '分类描述',
  `parent_id` BIGINT UNSIGNED DEFAULT 0 COMMENT '父分类ID (0表示顶级)',
  `sort_order` INT UNSIGNED DEFAULT 0 COMMENT '排序权重 (数值越大越靠前)',
  `icon` VARCHAR(100) DEFAULT NULL COMMENT '分类图标URL或类名',
  `status` TINYINT(1) UNSIGNED DEFAULT 1 COMMENT '状态: 0-禁用, 1-启用',
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_slug` (`slug`),
  KEY `idx_parent_id` (`parent_id`),
  KEY `idx_sort_order` (`sort_order`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文章分类表';

-- 将 posts 表的 category_id 关联到 categories 表
ALTER TABLE `posts`
ADD CONSTRAINT `fk_post_category` 
FOREIGN KEY (`category_id`) REFERENCES `categories`(`id`) 
ON DELETE SET NULL; -- 如果分类被删除，文章的分类ID自动变为NULL，而不是删除文章

-- 6. 管理员操作日志表
DROP TABLE IF EXISTS `admin_logs`;

CREATE TABLE `admin_logs` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `admin_id` BIGINT UNSIGNED NOT NULL COMMENT '管理员ID',
  `admin_name` VARCHAR(50) DEFAULT NULL COMMENT '管理员姓名 (冗余字段，方便查询)',
  
  -- 请求信息
  `action` VARCHAR(50) NOT NULL COMMENT '操作行为 (如: login, create_user, delete_post)',
  `detail` TEXT DEFAULT NULL COMMENT '操作详情 (如: 创建了哪个用户/文章等)',
  
  -- 环境信息
  `ip_address` VARCHAR(45) NOT NULL COMMENT 'IP地址 (支持IPv6)',
  `user_agent` VARCHAR(500) DEFAULT NULL COMMENT '浏览器/客户端标识',
  `os_info` VARCHAR(100) DEFAULT NULL COMMENT '操作系统信息 (可从UserAgent解析)',
  
  -- 时间
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '操作时间',

  PRIMARY KEY (`id`),
  KEY `idx_admin_id` (`admin_id`),
  KEY `idx_action` (`action`),
  KEY `idx_created_at` (`created_at`),
  KEY `idx_ip_address` (`ip_address`)
  
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='管理员操作日志表';

-- 7.文章点赞表
CREATE TABLE `post_likes` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `post_id` BIGINT UNSIGNED NOT NULL,
  `actor_key` VARCHAR(80) NOT NULL,
  `ip_address` VARCHAR(45) DEFAULT NULL,
  `user_agent` VARCHAR(255) DEFAULT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_post_actor` (`post_id`, `actor_key`),
  KEY `idx_ip_created` (`ip_address`, `created_at`),

  CONSTRAINT `fk_post_likes_post`
    FOREIGN KEY (`post_id`) REFERENCES `posts`(`id`)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 8.系统配置表
DROP TABLE IF EXISTS `settings`;

CREATE TABLE `settings` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `key` VARCHAR(100) NOT NULL COMMENT '配置键',
  `value` TEXT DEFAULT NULL COMMENT '配置值',
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_key` (`key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统配置表';