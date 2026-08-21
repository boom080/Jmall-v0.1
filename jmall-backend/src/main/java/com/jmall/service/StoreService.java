package com.jmall.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.jmall.common.BizCodeEnum;
import com.jmall.common.R;
import com.jmall.common.UserContext;
import com.jmall.dto.StoreCreateRequest;
import com.jmall.entity.Store;
import com.jmall.entity.Order;
import com.jmall.entity.Product;
import com.jmall.entity.User;
import com.jmall.repository.OrderRepository;
import com.jmall.repository.ProductRepository;
import com.jmall.repository.StoreRepository;
import com.jmall.repository.UserRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

@Service
public class StoreService {

    private final StoreRepository storeRepository;
    private final UserRepository userRepository;
    private final ProductRepository productRepository;
    private final OrderRepository orderRepository;
    private final AchievementService achievementService;

    public StoreService(StoreRepository storeRepository, UserRepository userRepository,
                        ProductRepository productRepository, OrderRepository orderRepository,
                        AchievementService achievementService) {
        this.storeRepository = storeRepository;
        this.userRepository = userRepository;
        this.productRepository = productRepository;
        this.orderRepository = orderRepository;
        this.achievementService = achievementService;
    }

    @Transactional
    public R create(StoreCreateRequest request) {
        Long userId = UserContext.getUserId();

        // Check if user already has a store
        LambdaQueryWrapper<Store> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(Store::getUserId, userId);
        if (storeRepository.selectCount(wrapper) > 0) {
            return R.error(10041, "user already owns a store");
        }

        Store store = new Store();
        store.setUserId(userId);
        store.setName(request.getName());
        store.setCategory(request.getCategory());
        store.setDescription(request.getDescription());
        store.setCreatedAt(LocalDateTime.now());
        store.setUpdatedAt(LocalDateTime.now());
        storeRepository.insert(store);

        // Link store to user
        User user = userRepository.selectById(userId);
        if (user != null) {
            user.setStoreId(store.getId());
            user.setUpdatedAt(LocalDateTime.now());
            userRepository.updateById(user);
        }

        // Check SHOP_OWNER achievement
        achievementService.checkShopOwner(userId);

        return R.ok(store);
    }

    public R getById(Long id) {
        Store store = storeRepository.selectById(id);
        if (store == null) {
            return R.error(BizCodeEnum.STORE_NOT_FOUND);
        }
        return R.ok(store);
    }

    public R getMyStore() {
        Long userId = UserContext.getUserId();
        LambdaQueryWrapper<Store> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(Store::getUserId, userId);
        Store store = storeRepository.selectOne(wrapper);
        if (store == null) {
            // Auto-create store for existing users who don't have one
            store = autoCreateStore(userId);
        }
        return R.ok(store);
    }

    public R getMyStats() {
        Long userId = UserContext.getUserId();
        LambdaQueryWrapper<Store> storeWrapper = new LambdaQueryWrapper<>();
        storeWrapper.eq(Store::getUserId, userId);
        Store store = storeRepository.selectOne(storeWrapper);
        if (store == null) {
            store = autoCreateStore(userId);
        }

        return getStatsForStore(store.getId());
    }

    public R getStats(Long storeId) {
        if (storeRepository.selectById(storeId) == null) {
            return R.error(BizCodeEnum.STORE_NOT_FOUND);
        }
        return getStatsForStore(storeId);
    }

    private R getStatsForStore(Long storeId) {
        LambdaQueryWrapper<Product> productWrapper = new LambdaQueryWrapper<>();
        productWrapper.eq(Product::getStoreId, storeId)
                .eq(Product::getStatus, "published");
        long productCount = productRepository.selectCount(productWrapper);

        LambdaQueryWrapper<Order> orderWrapper = new LambdaQueryWrapper<>();
        orderWrapper.eq(Order::getStoreId, storeId)
                .in(Order::getStatus, "paid", "shipped", "completed");
        List<Order> validOrders = orderRepository.selectList(orderWrapper);
        long totalSales = validOrders.stream()
                .mapToLong(order -> order.getQuantity() == null ? 0L : order.getQuantity())
                .sum();

        return R.ok(Map.of(
                "storeId", storeId,
                "productCount", productCount,
                "totalSales", totalSales,
                "totalOrders", validOrders.size()
        ));
    }

    private Store autoCreateStore(Long userId) {
        User user = userRepository.selectById(userId);
        String storeName = (user != null && user.getNickname() != null && !user.getNickname().isEmpty()
                ? user.getNickname() : "user") + "的店铺";

        Store store = new Store();
        store.setUserId(userId);
        store.setName(storeName);
        store.setCategory("其他");
        store.setDescription("欢迎光临！");
        store.setCreatedAt(LocalDateTime.now());
        store.setUpdatedAt(LocalDateTime.now());
        storeRepository.insert(store);

        // Link store to user
        if (user != null) {
            user.setStoreId(store.getId());
            user.setUpdatedAt(LocalDateTime.now());
            userRepository.updateById(user);
        }

        return store;
    }

    @Transactional
    public R update(Long id, StoreCreateRequest request) {
        Store store = storeRepository.selectById(id);
        if (store == null) {
            return R.error(BizCodeEnum.STORE_NOT_FOUND);
        }
        // Verify ownership
        Long userId = UserContext.getUserId();
        if (!store.getUserId().equals(userId)) {
            return R.error(BizCodeEnum.AUTH_ERROR);
        }

        store.setName(request.getName());
        store.setCategory(request.getCategory());
        store.setDescription(request.getDescription());
        if (request.getDecorationConfig() != null) {
            store.setDecorationConfig(request.getDecorationConfig());
        }
        store.setUpdatedAt(LocalDateTime.now());
        storeRepository.updateById(store);

        return R.ok(store);
    }

    public R getDecoration(Long id) {
        Store store = storeRepository.selectById(id);
        if (store == null) {
            return R.error(BizCodeEnum.STORE_NOT_FOUND);
        }
        return R.ok(store.getDecorationConfig());
    }

    public R list() {
        List<Store> stores = storeRepository.selectList(null);
        return R.ok(stores);
    }
}
