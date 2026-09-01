-- Jmall 业务数据库初始化
-- Target: MySQL 8.0

CREATE DATABASE IF NOT EXISTS jmall DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE jmall;

-- 用户表
CREATE TABLE IF NOT EXISTS jmall_user (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(64) NOT NULL UNIQUE,
    password_hash VARCHAR(256) NOT NULL,
    nickname VARCHAR(64) DEFAULT '',
    avatar VARCHAR(512) DEFAULT '',
    role VARCHAR(16) NOT NULL DEFAULT 'user' COMMENT 'user | admin',
    gold_balance BIGINT NOT NULL DEFAULT 1000 COMMENT '金币余额',
    points_balance BIGINT NOT NULL DEFAULT 0 COMMENT '积分余额',
    checkin_streak INT NOT NULL DEFAULT 0 COMMENT '连续签到天数',
    last_checkin DATE DEFAULT NULL,
    store_id BIGINT DEFAULT NULL COMMENT '关联店铺ID',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 店铺表
CREATE TABLE IF NOT EXISTS jmall_store (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL UNIQUE,
    name VARCHAR(120) NOT NULL,
    category VARCHAR(64) NOT NULL DEFAULT '' COMMENT '主营品类',
    description VARCHAR(500) DEFAULT '',
    decoration_config JSON DEFAULT NULL COMMENT '装修配置 JSON',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 商品表
CREATE TABLE IF NOT EXISTS jmall_product (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    store_id BIGINT NOT NULL,
    title VARCHAR(120) NOT NULL,
    subtitle VARCHAR(160) NOT NULL DEFAULT '' COMMENT '商品副标题/一句话卖点',
    category VARCHAR(64) NOT NULL DEFAULT '其他',
    description TEXT,
    price BIGINT NOT NULL DEFAULT 0 COMMENT '价格，单位分',
    images TEXT DEFAULT NULL COMMENT '图片URL，逗号分隔',
    style VARCHAR(32) NOT NULL DEFAULT 'taobao' COMMENT '展示风格',
    status VARCHAR(16) NOT NULL DEFAULT 'draft' COMMENT 'draft | published',
    view_count BIGINT NOT NULL DEFAULT 0,
    like_count BIGINT NOT NULL DEFAULT 0,
    sale_count BIGINT NOT NULL DEFAULT 0,
    ai_title VARCHAR(120) DEFAULT NULL,
    ai_selling_points JSON DEFAULT NULL,
    ai_detail TEXT,
    ai_style_previews JSON DEFAULT NULL COMMENT '多风格预览结果',
    market_insights JSON DEFAULT NULL COMMENT '市场洞察结果',
    compliance_result JSON DEFAULT NULL COMMENT '合规审查结果',
    ai_draft_meta JSON DEFAULT NULL COMMENT 'AI 草稿输入、图片来源与确认记录',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_store_id (store_id),
    INDEX idx_status (status),
    INDEX idx_category (category),
    INDEX idx_style (style)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 虚拟交易记录表
CREATE TABLE IF NOT EXISTS jmall_transaction (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    buyer_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,
    store_id BIGINT NOT NULL,
    amount BIGINT NOT NULL COMMENT '成交价，单位分',
    multiplier INT NOT NULL DEFAULT 1 COMMENT '暴击倍率 1-10',
    gold_earned BIGINT NOT NULL DEFAULT 0 COMMENT '买家获得的金币',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_buyer (buyer_id),
    INDEX idx_product (product_id),
    INDEX idx_store (store_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 签到记录
CREATE TABLE IF NOT EXISTS jmall_checkin (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    checkin_date DATE NOT NULL,
    gold_reward BIGINT NOT NULL DEFAULT 0,
    streak_day INT NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_user_date (user_id, checkin_date),
    INDEX idx_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 成就记录
CREATE TABLE IF NOT EXISTS jmall_achievement (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    achievement_key VARCHAR(64) NOT NULL,
    unlocked_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_user_achievement (user_id, achievement_key),
    INDEX idx_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 收藏表
CREATE TABLE IF NOT EXISTS jmall_collection (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_user_product (user_id, product_id),
    INDEX idx_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 评价表
CREATE TABLE IF NOT EXISTS jmall_review (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,
    content VARCHAR(500) DEFAULT '',
    rating INT NOT NULL DEFAULT 5 COMMENT '评分 1-5',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_product (product_id),
    INDEX idx_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 金币流水
CREATE TABLE IF NOT EXISTS jmall_gold_ledger (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    amount BIGINT NOT NULL COMMENT '变动金额，正为收入，负为支出',
    type VARCHAR(32) NOT NULL COMMENT 'checkin|purchase|sale|ai_cost|bonus|refund',
    description VARCHAR(256) DEFAULT '',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user (user_id),
    INDEX idx_type (type),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 购物车表
CREATE TABLE IF NOT EXISTS jmall_cart_item (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    buyer_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,
    quantity INT NOT NULL DEFAULT 1 COMMENT '数量',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_buyer_product (buyer_id, product_id),
    INDEX idx_buyer (buyer_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 订单表
CREATE TABLE IF NOT EXISTS jmall_order (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    buyer_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,
    store_id BIGINT NOT NULL,
    amount BIGINT NOT NULL COMMENT '实付金额，单位分',
    quantity INT NOT NULL DEFAULT 1,
    status VARCHAR(32) NOT NULL DEFAULT 'paid' COMMENT 'paid | shipped | completed | cancelled',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_buyer (buyer_id),
    INDEX idx_store (store_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 插入演示用户 (password: demo123)
INSERT IGNORE INTO jmall_user (id, username, password_hash, nickname, gold_balance) VALUES
(1, 'demo', '$2a$10$ApWLz304H2c4li2T6r8vZeatHeLKimdcQVwCA3hEuJtTQmZVTnQvm', '演示商家', 100000),
(2, 'shopper', '$2a$10$ApWLz304H2c4li2T6r8vZeatHeLKimdcQVwCA3hEuJtTQmZVTnQvm', '土豪玩家', 100000);
