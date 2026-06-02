CREATE DATABASE IF NOT EXISTS jrunmall_pms DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE jrunmall_pms;

CREATE TABLE IF NOT EXISTS pms_category (
    cat_id BIGINT PRIMARY KEY,
    name VARCHAR(64) NOT NULL,
    parent_cid BIGINT DEFAULT 0,
    cat_level INT DEFAULT 1,
    show_status INT DEFAULT 1,
    sort INT DEFAULT 0,
    icon VARCHAR(255) DEFAULT '',
    product_unit VARCHAR(32) DEFAULT '',
    product_count INT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS pms_sku_info (
    sku_id BIGINT PRIMARY KEY,
    spu_id BIGINT DEFAULT NULL,
    sku_name VARCHAR(255) DEFAULT '',
    sku_desc VARCHAR(2000) DEFAULT '',
    catalog_id BIGINT DEFAULT NULL,
    brand_id BIGINT DEFAULT NULL,
    sku_default_img VARCHAR(500) DEFAULT '',
    sku_title VARCHAR(255) DEFAULT '',
    sku_subtitle VARCHAR(500) DEFAULT '',
    price DECIMAL(18, 2) DEFAULT 0.00,
    sale_count BIGINT DEFAULT 0
);

INSERT INTO pms_category (cat_id, name, parent_cid, cat_level, show_status, sort, product_unit, product_count)
VALUES (225, 'Seckill Test Category', 0, 1, 1, 0, 'piece', 1)
ON DUPLICATE KEY UPDATE
    name = VALUES(name),
    show_status = VALUES(show_status),
    product_unit = VALUES(product_unit),
    product_count = VALUES(product_count);

INSERT INTO pms_sku_info (
    sku_id, spu_id, sku_name, sku_desc, catalog_id, brand_id,
    sku_default_img, sku_title, sku_subtitle, price, sale_count
) VALUES (
    14, 14001, 'Jrun Phone 14', 'Jrunmall seckill E2E test product', 225, 1,
    '/placeholders/products/default-product.svg', 'Jrun Phone 14', 'Seckill E2E test SKU', 1999.00, 0
) ON DUPLICATE KEY UPDATE
    sku_name = VALUES(sku_name),
    sku_desc = VALUES(sku_desc),
    catalog_id = VALUES(catalog_id),
    sku_default_img = VALUES(sku_default_img),
    sku_title = VALUES(sku_title),
    sku_subtitle = VALUES(sku_subtitle),
    price = VALUES(price);

