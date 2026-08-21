package com.jmall.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.jmall.common.R;
import com.jmall.dto.LeaderboardEntry;
import com.jmall.entity.Order;
import com.jmall.entity.Product;
import com.jmall.entity.Store;
import com.jmall.entity.Transaction;
import com.jmall.entity.User;
import com.jmall.repository.ProductRepository;
import com.jmall.repository.OrderRepository;
import com.jmall.repository.StoreRepository;
import com.jmall.repository.TransactionRepository;
import com.jmall.repository.UserRepository;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.data.redis.core.ZSetOperations;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.*;
import java.util.stream.Collectors;

@Service
public class LeaderboardService {

    private static final String REDIS_SPENDERS_KEY = "leaderboard:spenders:all";
    private static final String REDIS_SELLERS_KEY = "leaderboard:sellers:all";

    private final TransactionRepository transactionRepository;
    private final UserRepository userRepository;
    private final ProductRepository productRepository;
    private final OrderRepository orderRepository;
    private final StoreRepository storeRepository;
    private final RedisTemplate<String, Object> redisTemplate;

    public LeaderboardService(TransactionRepository transactionRepository,
                              UserRepository userRepository,
                              ProductRepository productRepository,
                              OrderRepository orderRepository,
                              StoreRepository storeRepository,
                              RedisTemplate<String, Object> redisTemplate) {
        this.transactionRepository = transactionRepository;
        this.userRepository = userRepository;
        this.productRepository = productRepository;
        this.orderRepository = orderRepository;
        this.storeRepository = storeRepository;
        this.redisTemplate = redisTemplate;
    }

    public R getTopSpenders(String period) {
        LocalDateTime since = getSinceDate(period);

        // Try Redis cache for "all" period
        if (since == null) {
            Set<ZSetOperations.TypedTuple<Object>> cached = redisTemplate.opsForZSet()
                    .reverseRangeWithScores(REDIS_SPENDERS_KEY, 0, 19);
            if (cached != null && !cached.isEmpty()) {
                List<LeaderboardEntry> entries = new ArrayList<>();
                int rank = 1;
                for (ZSetOperations.TypedTuple<Object> tuple : cached) {
                    Long userId = Long.valueOf(tuple.getValue().toString());
                    User user = userRepository.selectById(userId);
                    entries.add(LeaderboardEntry.builder()
                            .userId(userId)
                            .username(user != null ? user.getUsername() : "unknown")
                            .totalSpent(tuple.getScore().longValue())
                            .rank(rank++)
                            .build());
                }
                return R.ok(entries);
            }
        }

        // Fallback: query from DB
        List<Transaction> transactions;
        if (since != null) {
            LambdaQueryWrapper<Transaction> wrapper = new LambdaQueryWrapper<>();
            wrapper.ge(Transaction::getCreatedAt, since);
            transactions = transactionRepository.selectList(wrapper);
        } else {
            transactions = transactionRepository.selectList(null);
        }

        // Aggregate by buyer
        Map<Long, Long> buyerTotals = new HashMap<>();
        for (Transaction t : transactions) {
            buyerTotals.merge(t.getBuyerId(), t.getAmount(), Long::sum);
        }

        // Sort and build leaderboard
        List<LeaderboardEntry> entries = new ArrayList<>();
        int rank = 1;
        List<Map.Entry<Long, Long>> sorted = buyerTotals.entrySet().stream()
                .sorted(Map.Entry.<Long, Long>comparingByValue().reversed())
                .limit(20)
                .collect(Collectors.toList());

        for (Map.Entry<Long, Long> entry : sorted) {
            User user = userRepository.selectById(entry.getKey());
            entries.add(LeaderboardEntry.builder()
                    .userId(entry.getKey())
                    .username(user != null ? user.getUsername() : "unknown")
                    .totalSpent(entry.getValue())
                    .rank(rank++)
                    .build());
        }

        // Backfill Redis cache for "all" period
        if (since == null && !buyerTotals.isEmpty()) {
            for (Map.Entry<Long, Long> entry : buyerTotals.entrySet()) {
                redisTemplate.opsForZSet().add(REDIS_SPENDERS_KEY, entry.getKey().toString(), entry.getValue());
            }
        }

        return R.ok(entries);
    }

    public R getTopSellers(String period) {
        LocalDateTime since = getSinceDate(period);

        // Use the same authoritative valid-order source as store/dashboard
        // metrics. Product counters and legacy Redis scores may contain demo
        // seed values, so seller rankings never read them.
        List<Order> orders;
        if (since != null) {
            LambdaQueryWrapper<Order> wrapper = new LambdaQueryWrapper<>();
            wrapper.ge(Order::getCreatedAt, since)
                    .in(Order::getStatus, "paid", "shipped", "completed");
            orders = orderRepository.selectList(wrapper);
        } else {
            LambdaQueryWrapper<Order> wrapper = new LambdaQueryWrapper<>();
            wrapper.in(Order::getStatus, "paid", "shipped", "completed");
            orders = orderRepository.selectList(wrapper);
        }

        // Aggregate real item quantities by store.
        Map<Long, Long> storeSales = new HashMap<>();
        for (Order order : orders) {
            storeSales.merge(order.getStoreId(),
                    order.getQuantity() == null ? 0L : order.getQuantity().longValue(), Long::sum);
        }

        // Sort and build leaderboard with store/user names
        List<Map.Entry<Long, Long>> sorted = storeSales.entrySet().stream()
                .sorted(Map.Entry.<Long, Long>comparingByValue().reversed())
                .limit(20)
                .collect(Collectors.toList());

        List<Map<String, Object>> result = new ArrayList<>();
        int rank = 1;
        for (Map.Entry<Long, Long> entry : sorted) {
            Map<String, Object> item = new HashMap<>();
            item.put("storeId", entry.getKey());
            item.put("totalSales", entry.getValue());
            item.put("rank", rank);

            // Look up store name and owner
            Store store = storeRepository.selectById(entry.getKey());
            if (store != null) {
                item.put("storeName", store.getName());
                // Find store owner
                LambdaQueryWrapper<User> userWrapper = new LambdaQueryWrapper<>();
                userWrapper.eq(User::getStoreId, store.getId());
                User owner = userRepository.selectOne(userWrapper);
                if (owner != null) {
                    item.put("ownerName", owner.getNickname() != null && !owner.getNickname().isEmpty()
                            ? owner.getNickname() : owner.getUsername());
                }
            }

            rank++;
            result.add(item);
        }

        // Replace the old seller cache with order-derived values.
        if (since == null && !storeSales.isEmpty()) {
            redisTemplate.delete(REDIS_SELLERS_KEY);
            for (Map.Entry<Long, Long> entry : storeSales.entrySet()) {
                redisTemplate.opsForZSet().add(REDIS_SELLERS_KEY, entry.getKey().toString(), entry.getValue());
            }
        }

        return R.ok(result);
    }

    public R getTopProducts(String period) {
        LocalDateTime since = getSinceDate(period);

        LambdaQueryWrapper<Product> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(Product::getStatus, "published");
        if (since != null) {
            wrapper.ge(Product::getUpdatedAt, since);
        }
        wrapper.orderByDesc(Product::getSaleCount);
        wrapper.last("LIMIT 20");

        List<Product> products = productRepository.selectList(wrapper);

        List<Map<String, Object>> result = new ArrayList<>();
        int rank = 1;
        for (Product p : products) {
            Map<String, Object> item = new HashMap<>();
            item.put("id", p.getId());
            item.put("title", p.getTitle());
            item.put("category", p.getCategory());
            item.put("price", p.getPrice());
            item.put("saleCount", p.getSaleCount());
            item.put("images", p.getImages());
            item.put("storeId", p.getStoreId());
            item.put("rank", rank);
            Store store = storeRepository.selectById(p.getStoreId());
            if (store != null) {
                item.put("storeName", store.getName());
            }
            rank++;
            result.add(item);
        }
        return R.ok(result);
    }

    private LocalDateTime getSinceDate(String period) {
        if ("week".equals(period)) {
            return LocalDateTime.now().minusWeeks(1);
        } else if ("month".equals(period)) {
            return LocalDateTime.now().minusMonths(1);
        }
        return null; // all time
    }
}
