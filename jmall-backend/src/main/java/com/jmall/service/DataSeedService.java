package com.jmall.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.jmall.entity.Product;
import com.jmall.entity.Store;
import com.jmall.entity.User;
import com.jmall.repository.ProductRepository;
import com.jmall.repository.StoreRepository;
import com.jmall.repository.UserRepository;
import jakarta.annotation.PostConstruct;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.context.annotation.DependsOn;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.*;

/**
 * Seeds demo data when the database is empty or has very few products.
 * Creates stores for demo users and inserts sample products across categories.
 */
@Service
@DependsOn("schemaMigrationService")
public class DataSeedService {

    private static final Logger log = LoggerFactory.getLogger(DataSeedService.class);

    private final ProductRepository productRepository;
    private final StoreRepository storeRepository;
    private final UserRepository userRepository;
    private final ImageGenerationService imageService;

    public DataSeedService(ProductRepository productRepository,
                           StoreRepository storeRepository,
                           UserRepository userRepository,
                           ImageGenerationService imageService) {
        this.productRepository = productRepository;
        this.storeRepository = storeRepository;
        this.userRepository = userRepository;
        this.imageService = imageService;
    }

    @PostConstruct
    @Transactional
    public void seed() {
        long count = productRepository.selectCount(null);
        if (count >= 10) {
            log.info("DataSeedService: {} products exist, skipping seed", count);
            return;
        }

        log.info("DataSeedService: only {} products, seeding demo data...", count);

        // Ensure demo stores exist for all demo users
        Store store1 = ensureStore(1L, "Demo 品质好物馆", "食品饮料", "AI 电商模拟平台官方演示店铺");
        Store store2 = ensureStore(2L, "shopper的杂货铺", "食品饮料", "好喝不贵，天天特价");
        Store store3 = ensureStore(3L, "demouser时尚馆", "服饰鞋包", "潮流穿搭，品质之选");
        Store store4 = ensureStore(4L, "Admin 数码旗舰店", "数码家电", "品质数码产品，官方授权正品保障");
        Store store5 = ensureStore(5L, "e2e精选好物", "数码家电", "品质数码，官方正品保证");

        List<Store> stores = List.of(store1, store2, store3, store4, store5);

        // Products grouped by (category, style) for variety
        List<ProductSeed> seeds = List.of(
            // ---- 手机数码 ----
            new ProductSeed("华为Mate 80 Pro 5G旗舰手机", "手机数码", "搭载麒麟9100芯片，6.8英寸OLED曲面屏，120Hz高刷，5000mAh大电池", 699900L, "jd"),
            new ProductSeed("小米15 Ultra 徕卡影像旗舰", "手机数码", "徕卡光学镜头，1英寸大底传感器，骁龙8Gen4，90W快充", 599900L, "jd"),
            new ProductSeed("OPPO Find X8 Pro AI影像手机", "手机数码", "双潜望长焦，AI消除路人，哈苏色彩，4800mAh超长续航", 549900L, "taobao"),
            new ProductSeed("vivo X200 Pro 蔡司超级长焦", "手机数码", "蔡司APO超级长焦，天玑9400，120W闪充，IP68防水", 529900L, "taobao"),

            // ---- 茶叶 ----
            new ProductSeed("明前特级西湖龙井礼盒 50g", "茶叶", "2025年明前头采，西湖核心产区，非遗手工炒制，豆香浓郁", 39800L, "taobao"),
            new ProductSeed("安溪铁观音清香型 250g", "茶叶", "高山茶园，传统半发酵工艺，兰花香韵，回甘持久", 12800L, "taobao"),
            new ProductSeed("云南普洱茶 熟茶饼 357g", "茶叶", "勐海古树春茶，5年陈化，醇厚顺滑，送礼收藏皆宜", 25800L, "pinduoduo"),
            new ProductSeed("武夷山金骏眉红茶 100g", "茶叶", "桐木关核心产区，全芽制作，蜜香薯香，世界红茶典范", 19800L, "xiaohongshu"),

            // ---- 厨房电器 ----
            new ProductSeed("全自动空气炸锅 AF-508 5.5L", "厨房电器", "360°热风循环，少油健康炸，8大智能菜单，不粘内胆", 25900L, "xiaohongshu"),
            new ProductSeed("智能IH电饭煲 4L", "厨房电器", "日本进口IH电磁加热，24小时预约，球釜内胆，3mm加厚", 39900L, "jd"),
            new ProductSeed("迷你破壁机 600ml", "厨房电器", "免泡直打，8叶刀头，一键清洗，豆浆米糊辅食果汁", 19900L, "pinduoduo"),
            new ProductSeed("家用净水器 超滤直饮", "厨房电器", "五级RO反渗透，600G大通量，智能屏显，换芯提醒", 149900L, "jd"),

            // ---- 服饰鞋包 ----
            new ProductSeed("春季新款男士商务休闲夹克", "服饰鞋包", "高支棉面料，免烫抗皱，修身版型，通勤百搭", 29900L, "taobao"),
            new ProductSeed("女士真皮单肩斜挎包", "服饰鞋包", "头层牛皮，五金锁扣，大容量设计，通勤休闲两用", 35900L, "xiaohongshu"),
            new ProductSeed("纯棉情侣款卫衣 加绒保暖", "服饰鞋包", "纯棉毛巾底，加厚加绒，宽松版型，多色可选", 12900L, "pinduoduo"),
            new ProductSeed("运动跑鞋 男士轻便减震", "服饰鞋包", "飞织鞋面，爆米花中底，轻盈透气，橡胶防滑大底", 19900L, "jd"),

            // ---- 食品饮料 ----
            new ProductSeed("良品铺子每日坚果礼盒 750g", "食品饮料", "7种坚果果干，独立锁鲜包装，每日营养搭配", 8990L, "taobao"),
            new ProductSeed("三只松鼠巨型零食大礼包 2kg", "食品饮料", "18款人气零食组合，追剧办公解馋，送礼大礼包", 12990L, "pinduoduo"),
            new ProductSeed("安佳进口全脂纯牛奶 250ml×24盒", "食品饮料", "新西兰原装进口，3.5g蛋白质，营养早餐必备", 7990L, "jd")
        );

        int idx = 0;
        for (ProductSeed seed : seeds) {
            Store store = stores.get(idx % stores.size());

            // First product in each store gets a generated image, rest use placeholder
            String imageUrl = imageService.generate(seed.title, seed.category);
            String images = "[\"" + imageUrl + "\"]";

            Product product = new Product();
            product.setStoreId(store.getId());
            product.setTitle(seed.title);
            product.setSubtitle(seed.description);
            product.setCategory(seed.category);
            product.setDescription(seed.description);
            product.setPrice(seed.price);
            product.setImages(images);
            product.setStyle(seed.style);
            product.setStatus("published");
            product.setViewCount(0L);
            product.setSaleCount(0L);
            product.setLikeCount(0L);
            product.setCreatedAt(LocalDateTime.now());
            product.setUpdatedAt(LocalDateTime.now());
            productRepository.insert(product);

            idx++;
        }

        log.info("DataSeedService: seeded {} products across {} stores", idx, stores.size());
    }

    private Store ensureStore(Long userId, String name, String category, String desc) {
        LambdaQueryWrapper<Store> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(Store::getUserId, userId);
        Store existing = storeRepository.selectOne(wrapper);
        if (existing != null) {
            return existing;
        }

        // Check user exists
        User user = userRepository.selectById(userId);
        if (user == null) {
            log.warn("DataSeedService: user {} not found, skipping store creation", userId);
            // Use the first existing store as fallback
            List<Store> stores = storeRepository.selectList(null);
            if (!stores.isEmpty()) return stores.get(0);
            throw new RuntimeException("No users or stores available for seeding");
        }

        Store store = new Store();
        store.setUserId(userId);
        store.setName(name);
        store.setCategory(category);
        store.setDescription(desc);
        store.setCreatedAt(LocalDateTime.now());
        store.setUpdatedAt(LocalDateTime.now());
        storeRepository.insert(store);

        // Link store to user
        user.setStoreId(store.getId());
        user.setUpdatedAt(LocalDateTime.now());
        userRepository.updateById(user);

        log.info("DataSeedService: created store '{}' for user {}", name, userId);
        return store;
    }

    // ---- Inner class for seed data ----
    private record ProductSeed(String title, String category, String description, Long price, String style) {}
}
