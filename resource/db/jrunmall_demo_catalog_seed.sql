SET NAMES utf8mb4;
USE jrunmall_pms;

INSERT INTO pms_category (cat_id, name, parent_cid, cat_level, show_status, sort, product_unit, product_count)
VALUES
  (3, '家用电器', 0, 1, 1, 3, '件', 0),
  (6, '电脑办公', 0, 1, 1, 6, '件', 0),
  (7, '厨具', 0, 1, 1, 7, '件', 0),
  (14, '食品饮料', 0, 1, 1, 14, '件', 0),
  (17, '运动健康', 0, 1, 1, 17, '件', 0),
  (20, '生鲜', 0, 1, 1, 20, '件', 0)
ON DUPLICATE KEY UPDATE
  name = VALUES(name),
  show_status = VALUES(show_status),
  product_unit = VALUES(product_unit);

INSERT INTO pms_spu_info
  (id, spu_name, spu_description, catalog_id, brand_id, weight, publish_status, create_time, update_time)
VALUES
  (900001, '每日鲜语低温鲜牛奶 950ml', '低温冷链鲜奶，适合早餐、咖啡和烘焙场景。', 14, 0, 0.9500, 1, NOW(), NOW()),
  (900002, '山姆同款坚果燕麦脆 600g', '混合坚果与谷物烘焙，适合早餐和办公室加餐。', 14, 0, 0.6000, 1, NOW(), NOW()),
  (900003, '云南高山蓝莓 12盒装', '产地直采蓝莓，果粉完整，冷链配送。', 20, 0, 1.2000, 1, NOW(), NOW()),
  (900004, '挪威三文鱼切片 500g', '冷冻三文鱼切片，适合轻食、寿司和煎烤。', 20, 0, 0.5000, 1, NOW(), NOW()),
  (900005, '米家空气净化器 4 Pro', '适合客厅和卧室的空气净化设备，支持智能联动。', 3, 0, 6.8000, 1, NOW(), NOW()),
  (900006, '戴森 V12 Detect Slim 吸尘器', '轻量化无线吸尘器，适合地板、地毯和缝隙清洁。', 3, 0, 2.2000, 1, NOW(), NOW()),
  (900007, 'ThinkPad X1 Carbon 14英寸轻薄本', '商务办公轻薄本，适合移动办公、文档和会议场景。', 6, 0, 1.1200, 1, NOW(), NOW()),
  (900008, '罗技 MX Keys S 无线键盘', '低噪薄膜键盘，支持多设备切换。', 6, 0, 0.8100, 1, NOW(), NOW()),
  (900009, '双立人不锈钢炒锅 32cm', '日常煎炒炖煮锅具，适配燃气和电磁炉。', 7, 0, 1.8000, 1, NOW(), NOW()),
  (900010, '膳魔师保温杯 500ml', '通勤随行保温杯，适合咖啡、茶和温水。', 7, 0, 0.3500, 1, NOW(), NOW()),
  (900011, 'Keep 智能动感单车 C1', '家庭有氧训练设备，适合室内骑行课程。', 17, 0, 32.0000, 1, NOW(), NOW()),
  (900012, '佳明 Forerunner 265 运动腕表', '跑步、骑行和健康监测腕表，适合长期训练记录。', 17, 0, 0.0470, 1, NOW(), NOW())
ON DUPLICATE KEY UPDATE
  spu_name = VALUES(spu_name),
  spu_description = VALUES(spu_description),
  catalog_id = VALUES(catalog_id),
  publish_status = VALUES(publish_status),
  update_time = NOW();

INSERT INTO pms_spu_info_desc (spu_id, decript)
VALUES
  (900001, '低温冷链鲜奶，口感清爽，适合家庭早餐。'),
  (900002, '坚果、燕麦、冻干水果混合烘焙，开袋即食。'),
  (900003, '云南产地蓝莓，适合水果拼盘、酸奶杯和烘焙。'),
  (900004, '冷冻三文鱼切片，解冻后可煎烤或制作轻食。'),
  (900005, '智能空气净化设备，适合卧室和客厅连续运行。'),
  (900006, '轻量化无线吸尘器，适合家庭深度清洁。'),
  (900007, '高端商务轻薄本，适合通勤、会议和远程办公。'),
  (900008, '多设备无线键盘，适合办公桌面和移动工位。'),
  (900009, '不锈钢炒锅，适合中式家庭厨房高频使用。'),
  (900010, '通勤保温杯，适合咖啡、茶饮和温水。'),
  (900011, '家庭智能动感单车，适合有氧训练和课程跟练。'),
  (900012, '运动腕表，覆盖跑步、骑行、睡眠和心率监测。')
ON DUPLICATE KEY UPDATE decript = VALUES(decript);

INSERT INTO pms_sku_info
  (sku_id, spu_id, sku_name, sku_desc, catalog_id, brand_id, sku_default_img, sku_title, sku_subtitle, price, sale_count)
VALUES
  (900001, 900001, '每日鲜语低温鲜牛奶 950ml', '低温冷链鲜奶，72小时内发货。', 14, 0, 'https://images.unsplash.com/photo-1563636619-e9143da7973b?auto=format&fit=crop&w=900&q=80', '每日鲜语低温鲜牛奶 950ml 家庭早餐装', '低温冷链 | 早餐咖啡 | 顺丰冷运', 19.90, 3200),
  (900002, 900002, '山姆同款坚果燕麦脆 600g', '坚果燕麦脆，办公室和早餐场景适用。', 14, 0, 'https://images.unsplash.com/photo-1517093157656-b9eccef91cb1?auto=format&fit=crop&w=900&q=80', '山姆同款坚果燕麦脆 600g 早餐冲饮搭档', '混合坚果 | 谷物烘焙 | 独立密封', 49.90, 2100),
  (900003, 900003, '云南高山蓝莓 12盒装', '高山蓝莓，产地直采冷链配送。', 20, 0, 'https://images.unsplash.com/photo-1498557850523-fd3d118b962e?auto=format&fit=crop&w=900&q=80', '云南高山蓝莓 12盒装 新鲜水果礼盒', '产地直采 | 冷链配送 | 果粉完整', 89.00, 1800),
  (900004, 900004, '挪威三文鱼切片 500g', '三文鱼切片，适合轻食和煎烤。', 20, 0, 'https://images.unsplash.com/photo-1580476262798-bddd9f4b7369?auto=format&fit=crop&w=900&q=80', '挪威三文鱼切片 500g 冷冻海鲜', '低温锁鲜 | 轻食优选 | 家庭装', 129.00, 960),
  (900005, 900005, '米家空气净化器 4 Pro', '大空间空气净化器，支持智能联动。', 3, 0, 'https://images.unsplash.com/photo-1558089687-f282ffcbc126?auto=format&fit=crop&w=900&q=80', '米家空气净化器 4 Pro 家用智能除醛', '智能联动 | 低噪运行 | 客厅卧室', 1299.00, 1480),
  (900006, 900006, '戴森 V12 Detect Slim 吸尘器', '无线吸尘器，适合地面、缝隙和床褥清洁。', 3, 0, 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?auto=format&fit=crop&w=900&q=80', '戴森 V12 Detect Slim 轻量无线吸尘器', '轻量机身 | 多刷头 | 家庭深度清洁', 3990.00, 620),
  (900007, 900007, 'ThinkPad X1 Carbon 14英寸轻薄本', '商务轻薄本，适合会议和移动办公。', 6, 0, 'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?auto=format&fit=crop&w=900&q=80', 'ThinkPad X1 Carbon 14英寸商务轻薄本', '轻薄机身 | 长续航 | 商务办公', 9999.00, 740),
  (900008, 900008, '罗技 MX Keys S 无线键盘', '多设备无线键盘，适合办公桌面。', 6, 0, 'https://images.unsplash.com/photo-1587829741301-dc798b83add3?auto=format&fit=crop&w=900&q=80', '罗技 MX Keys S 无线键盘 多设备切换', '低噪输入 | 多设备 | 背光按键', 699.00, 2600),
  (900009, 900009, '双立人不锈钢炒锅 32cm', '不锈钢炒锅，适合日常煎炒炖煮。', 7, 0, 'https://images.unsplash.com/photo-1556911220-bff31c812dba?auto=format&fit=crop&w=900&q=80', '双立人不锈钢炒锅 32cm 家用厨房锅具', '不锈钢锅体 | 电磁炉适用 | 易清洁', 459.00, 1180),
  (900010, 900010, '膳魔师保温杯 500ml', '通勤保温杯，适合咖啡、茶和温水。', 7, 0, 'https://images.unsplash.com/photo-1523362628745-0c100150b504?auto=format&fit=crop&w=900&q=80', '膳魔师保温杯 500ml 通勤随行杯', '长效保温 | 轻量杯身 | 防漏杯盖', 189.00, 4300),
  (900011, 900011, 'Keep 智能动感单车 C1', '家庭有氧训练设备，适合课程跟练。', 17, 0, 'https://images.unsplash.com/photo-1599058917212-d750089bc07e?auto=format&fit=crop&w=900&q=80', 'Keep 智能动感单车 C1 家庭有氧训练', '静音骑行 | 课程跟练 | 家庭健身', 1999.00, 680),
  (900012, 900012, '佳明 Forerunner 265 运动腕表', '跑步训练和健康监测腕表。', 17, 0, 'https://images.unsplash.com/photo-1508685096489-7aacd43bd3b1?auto=format&fit=crop&w=900&q=80', '佳明 Forerunner 265 跑步运动腕表', '训练计划 | 心率监测 | 多运动模式', 3480.00, 520)
ON DUPLICATE KEY UPDATE
  spu_id = VALUES(spu_id),
  sku_name = VALUES(sku_name),
  sku_desc = VALUES(sku_desc),
  catalog_id = VALUES(catalog_id),
  sku_default_img = VALUES(sku_default_img),
  sku_title = VALUES(sku_title),
  sku_subtitle = VALUES(sku_subtitle),
  price = VALUES(price),
  sale_count = VALUES(sale_count);
