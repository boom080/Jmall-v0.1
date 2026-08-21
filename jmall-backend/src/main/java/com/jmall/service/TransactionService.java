package com.jmall.service;

import com.jmall.common.BizCodeEnum;
import com.jmall.common.R;
import com.jmall.common.UserContext;
import com.jmall.entity.Product;
import com.jmall.entity.Order;
import com.jmall.entity.Store;
import com.jmall.entity.Transaction;
import com.jmall.entity.User;
import com.jmall.repository.ProductRepository;
import com.jmall.repository.OrderRepository;
import com.jmall.repository.StoreRepository;
import com.jmall.repository.TransactionRepository;
import com.jmall.repository.UserRepository;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

@Service
public class TransactionService {

    private static final String REDIS_SPENDERS_KEY = "leaderboard:spenders:all";
    private static final String REDIS_SELLERS_KEY = "leaderboard:sellers:all";

    private final TransactionRepository transactionRepository;
    private final OrderRepository orderRepository;
    private final ProductRepository productRepository;
    private final StoreRepository storeRepository;
    private final UserRepository userRepository;
    private final UserService userService;
    private final ProductService productService;
    private final AchievementService achievementService;
    private final RedisTemplate<String, Object> redisTemplate;

    public TransactionService(TransactionRepository transactionRepository,
                              OrderRepository orderRepository,
                              ProductRepository productRepository,
                              StoreRepository storeRepository,
                              UserRepository userRepository,
                              UserService userService,
                              ProductService productService,
                              AchievementService achievementService,
                              RedisTemplate<String, Object> redisTemplate) {
        this.transactionRepository = transactionRepository;
        this.orderRepository = orderRepository;
        this.productRepository = productRepository;
        this.storeRepository = storeRepository;
        this.userRepository = userRepository;
        this.userService = userService;
        this.productService = productService;
        this.achievementService = achievementService;
        this.redisTemplate = redisTemplate;
    }

    @Transactional
    public R purchase(Long productId) {
        Long buyerId = UserContext.getUserId();

        // Get product
        Product product = productRepository.selectById(productId);
        if (product == null) {
            return R.error(BizCodeEnum.PRODUCT_NOT_FOUND);
        }
        if (!"published".equals(product.getStatus())) {
            return R.error(10031, "product is not available for purchase");
        }

        // Check buyer is not the store owner
        Store store = storeRepository.selectById(product.getStoreId());
        if (store != null && store.getUserId().equals(buyerId)) {
            return R.error(10032, "cannot purchase your own product");
        }

        long priceInFen = product.getPrice();
        long goldCost = Math.max(1, priceInFen / 100);  // 1 gold = 1 yuan, min 1 gold

        // Check balance
        User buyer = userRepository.selectById(buyerId);
        if (buyer == null) {
            return R.error(BizCodeEnum.USER_NOT_FOUND);
        }
        if (buyer.getGoldBalance() < goldCost) {
            return R.error(10033, "金币不足！当前余额: " + buyer.getGoldBalance() + "金币，商品价格: " + goldCost + "金币");
        }

        // Deduct gold from buyer
        userService.deductGold(buyerId, goldCost, "purchase",
                "购买商品: " + product.getTitle());

        // Add gold to seller (store owner)
        if (store != null) {
            userService.addGold(store.getUserId(), goldCost, "sale",
                    "售出商品: " + product.getTitle());
        }

        // Create transaction record
        Transaction transaction = new Transaction();
        transaction.setBuyerId(buyerId);
        transaction.setProductId(productId);
        transaction.setStoreId(product.getStoreId());
        transaction.setAmount(priceInFen);
        transaction.setMultiplier(1);
        transaction.setGoldEarned(goldCost); // Seller's earning in yuan
        transaction.setCreatedAt(LocalDateTime.now());
        transactionRepository.insert(transaction);

        // A direct purchase is still an order. Persist the same business fact
        // used by cart checkout so merchant metrics have one authoritative source.
        Order order = new Order();
        order.setBuyerId(buyerId);
        order.setProductId(productId);
        order.setStoreId(product.getStoreId());
        order.setAmount(priceInFen);
        order.setQuantity(1);
        order.setStatus("paid");
        order.setCreatedAt(LocalDateTime.now());
        order.setUpdatedAt(LocalDateTime.now());
        orderRepository.insert(order);

        // Increment sale count
        productService.incrementSaleCount(productId, 1);

        // Update Redis leaderboard caches
        try {
            redisTemplate.opsForZSet().incrementScore(REDIS_SPENDERS_KEY, buyerId.toString(), goldCost);
            redisTemplate.opsForZSet().incrementScore(REDIS_SELLERS_KEY, product.getStoreId().toString(), 1);
        } catch (Exception e) {
            // Redis failure should not block the purchase
        }

        // Check achievement unlocks
        achievementService.checkAndUnlock(buyerId);
        if (store != null) {
            achievementService.checkAndUnlock(store.getUserId());
        }

        Map<String, Object> result = new HashMap<>();
        result.put("amount", priceInFen);
        result.put("goldDeducted", goldCost);
        result.put("transactionId", transaction.getId());
        result.put("orderId", order.getId());
        result.put("newBalance", buyer.getGoldBalance() - goldCost);
        return R.ok("purchase successful", result);
    }
}
