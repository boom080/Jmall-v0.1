CREATE DATABASE IF NOT EXISTS jrunmall_commerce DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE jrunmall_commerce;

CREATE TABLE IF NOT EXISTS jrunmall_user_order (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    order_sn VARCHAR(64) NOT NULL UNIQUE,
    user_id BIGINT NOT NULL,
    username VARCHAR(64) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'CREATED',
    total_amount DECIMAL(18, 2) NOT NULL DEFAULT 0.00,
    total_quantity INT NOT NULL DEFAULT 0,
    note VARCHAR(255) DEFAULT '',
    order_source VARCHAR(32) NOT NULL DEFAULT 'normal',
    biz_token VARCHAR(128) DEFAULT NULL,
    address_id BIGINT DEFAULT NULL,
    receiver_name VARCHAR(64) DEFAULT '',
    receiver_phone VARCHAR(32) DEFAULT '',
    receiver_address VARCHAR(255) DEFAULT '',
    created_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    payment_time DATETIME NULL,
    updated_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_jrunmall_order_biz_token (biz_token)
);

CREATE TABLE IF NOT EXISTS jrunmall_user_order_item (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    order_id BIGINT NOT NULL,
    order_sn VARCHAR(64) NOT NULL,
    sku_id BIGINT NOT NULL,
    spu_id BIGINT NULL,
    title VARCHAR(255) NOT NULL,
    category VARCHAR(120) DEFAULT '',
    cover_url VARCHAR(500) DEFAULT '',
    summary VARCHAR(255) DEFAULT '',
    price DECIMAL(18, 2) NOT NULL DEFAULT 0.00,
    quantity INT NOT NULL DEFAULT 1,
    line_amount DECIMAL(18, 2) NOT NULL DEFAULT 0.00,
    created_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_jrunmall_order_id (order_id),
    INDEX idx_jrunmall_order_sn (order_sn)
);

