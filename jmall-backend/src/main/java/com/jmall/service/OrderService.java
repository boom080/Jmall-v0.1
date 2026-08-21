package com.jmall.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.jmall.common.BizCodeEnum;
import com.jmall.common.R;
import com.jmall.common.UserContext;
import com.jmall.entity.*;
import com.jmall.repository.*;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.*;

@Service
public class OrderService {

    private final OrderRepository orderRepository;
    private final CartItemRepository cartItemRepository;
    private final ProductRepository productRepository;
    private final StoreRepository storeRepository;
    private final TransactionRepository transactionRepository;
    private final UserRepository userRepository;
    private final ProductService productService;
    private final UserService userService;

    public OrderService(OrderRepository orderRepository,
                        CartItemRepository cartItemRepository,
                        ProductRepository productRepository,
                        StoreRepository storeRepository,
                        TransactionRepository transactionRepository,
                        UserRepository userRepository,
                        ProductService productService,
                        UserService userService) {
        this.orderRepository = orderRepository;
        this.cartItemRepository = cartItemRepository;
        this.productRepository = productRepository;
        this.storeRepository = storeRepository;
        this.transactionRepository = transactionRepository;
        this.userRepository = userRepository;
        this.productService = productService;
        this.userService = userService;
    }

    @Transactional
    public R createFromCart() {
        Long buyerId = UserContext.getUserId();

        // Get cart items
        LambdaQueryWrapper<CartItem> cartWrapper = new LambdaQueryWrapper<>();
        cartWrapper.eq(CartItem::getBuyerId, buyerId);
        List<CartItem> cartItems = cartItemRepository.selectList(cartWrapper);
        if (cartItems.isEmpty()) {
            return R.error(10090, "购物车是空的");
        }

        // Calculate total amount
        long totalGoldCost = 0L;
        List<Map<String, Object>> validItems = new ArrayList<>();
        for (CartItem item : cartItems) {
            Product product = productRepository.selectById(item.getProductId());
            if (product == null) {
                return R.error(10031, "购物车中有商品不存在，请移除后重试");
            }
            if (!"published".equals(product.getStatus())) {
                return R.error(10031, "商品「" + product.getTitle() + "」已下架，请移除后重试");
            }
            Store store = storeRepository.selectById(product.getStoreId());
            if (store != null && store.getUserId().equals(buyerId)) {
                return R.error(10092, "不能购买自己店铺的商品「" + product.getTitle() + "」，请先从购物车移除");
            }
            long priceInFen = product.getPrice() * item.getQuantity();
            long goldCost = Math.max(1, priceInFen / 100);  // 1 gold = 1 yuan
            totalGoldCost += goldCost;
            validItems.add(Map.of("item", item, "product", product, "store", store, "priceInFen", priceInFen, "goldCost", goldCost));
        }

        if (validItems.isEmpty()) {
            return R.error(10091, "购物车中没有可结算商品");
        }

        // Check balance
        User buyer = userRepository.selectById(buyerId);
        if (buyer == null) {
            return R.error(BizCodeEnum.USER_NOT_FOUND);
        }
        if (buyer.getGoldBalance() < totalGoldCost) {
            return R.error(10033, "金币不足！当前余额: " + buyer.getGoldBalance() + "金币，需要: " + totalGoldCost + "金币");
        }

        // Deduct total gold from buyer
        userService.deductGold(buyerId, totalGoldCost, "purchase",
                "购物车结算，共" + validItems.size() + "件商品");

        List<Map<String, Object>> orders = new ArrayList<>();

        for (Map<String, Object> vi : validItems) {
            CartItem item = (CartItem) vi.get("item");
            Product product = (Product) vi.get("product");
            Store store = (Store) vi.get("store");
            long priceInFen = (long) vi.get("priceInFen");
            long goldCost = (long) vi.get("goldCost");

            // Create order
            Order order = new Order();
            order.setBuyerId(buyerId);
            order.setProductId(product.getId());
            order.setStoreId(product.getStoreId());
            order.setAmount(priceInFen);
            order.setQuantity(item.getQuantity());
            order.setStatus("paid");
            order.setCreatedAt(LocalDateTime.now());
            order.setUpdatedAt(LocalDateTime.now());
            orderRepository.insert(order);

            // Create transaction record
            Transaction transaction = new Transaction();
            transaction.setBuyerId(buyerId);
            transaction.setProductId(product.getId());
            transaction.setStoreId(product.getStoreId());
            transaction.setAmount(priceInFen);
            transaction.setMultiplier(1);
            transaction.setGoldEarned(goldCost);
            transaction.setCreatedAt(LocalDateTime.now());
            transactionRepository.insert(transaction);

            // Add gold to seller
            if (store != null) {
                userService.addGold(store.getUserId(), goldCost, "sale",
                        "售出商品: " + product.getTitle());
            }

            // Increment sale count
            productService.incrementSaleCount(product.getId(), item.getQuantity());

            Map<String, Object> orderInfo = new HashMap<>();
            orderInfo.put("orderId", order.getId());
            orderInfo.put("productTitle", product.getTitle());
            orderInfo.put("amount", priceInFen);
            orderInfo.put("goldCost", goldCost);
            orderInfo.put("quantity", item.getQuantity());
            orders.add(orderInfo);
        }

        // Clear cart
        cartItemRepository.delete(cartWrapper);

        Map<String, Object> result = new HashMap<>();
        result.put("orders", orders);
        result.put("totalOrders", orders.size());
        result.put("totalGoldCost", totalGoldCost);
        result.put("newBalance", buyer.getGoldBalance() - totalGoldCost);
        return R.ok("checkout complete", result);
    }

    public R list() {
        Long buyerId = UserContext.getUserId();
        LambdaQueryWrapper<Order> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(Order::getBuyerId, buyerId);
        wrapper.orderByDesc(Order::getCreatedAt);
        List<Order> orders = orderRepository.selectList(wrapper);

        List<Map<String, Object>> result = new ArrayList<>();
        for (Order order : orders) {
            Product product = productRepository.selectById(order.getProductId());
            Map<String, Object> entry = new HashMap<>();
            entry.put("id", order.getId());
            entry.put("productId", order.getProductId());
            entry.put("productTitle", product != null ? product.getTitle() : "unknown");
            entry.put("productImage", product != null && product.getImages() != null ? product.getImages() : "");
            entry.put("amount", order.getAmount());
            entry.put("quantity", order.getQuantity());
            entry.put("status", order.getStatus());
            entry.put("createdAt", order.getCreatedAt());
            result.add(entry);
        }
        return R.ok(result);
    }
}
