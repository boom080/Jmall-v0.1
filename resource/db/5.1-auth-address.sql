CREATE DATABASE IF NOT EXISTS jrunmall_commerce DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE jrunmall_commerce;

SET @db_name = DATABASE();

SET @sql = IF (
    EXISTS (
        SELECT 1
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = @db_name
          AND TABLE_NAME = 'jrunmall_user_order'
          AND COLUMN_NAME = 'address_id'
    ),
    'SELECT ''address_id exists''',
    'ALTER TABLE jrunmall_user_order ADD COLUMN address_id BIGINT DEFAULT NULL AFTER biz_token'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF (
    EXISTS (
        SELECT 1
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = @db_name
          AND TABLE_NAME = 'jrunmall_user_order'
          AND COLUMN_NAME = 'receiver_name'
    ),
    'SELECT ''receiver_name exists''',
    'ALTER TABLE jrunmall_user_order ADD COLUMN receiver_name VARCHAR(64) DEFAULT NULL AFTER address_id'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF (
    EXISTS (
        SELECT 1
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = @db_name
          AND TABLE_NAME = 'jrunmall_user_order'
          AND COLUMN_NAME = 'receiver_phone'
    ),
    'SELECT ''receiver_phone exists''',
    'ALTER TABLE jrunmall_user_order ADD COLUMN receiver_phone VARCHAR(32) DEFAULT NULL AFTER receiver_name'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF (
    EXISTS (
        SELECT 1
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = @db_name
          AND TABLE_NAME = 'jrunmall_user_order'
          AND COLUMN_NAME = 'receiver_address'
    ),
    'SELECT ''receiver_address exists''',
    'ALTER TABLE jrunmall_user_order ADD COLUMN receiver_address VARCHAR(255) DEFAULT NULL AFTER receiver_phone'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

