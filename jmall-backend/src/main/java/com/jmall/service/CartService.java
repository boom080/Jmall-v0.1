package com.jmall.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.jmall.common.BizCodeEnum;
import com.jmall.common.R;
import com.jmall.common.UserContext;
import com.jmall.entity.CartItem;
import com.jmall.entity.Product;
import com.jmall.entity.Store;
import com.jmall.repository.CartItemRepository;
import com.jmall.repository.ProductRepository;
import com.jmall.repository.StoreRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.*;

@Service
public class CartService {

    private final CartItemRepository cartItemRepository;
    private final ProductRepository productRepository;
    private final StoreRepository storeRepository;

    public CartService(CartItemRepository cartItemRepository, ProductRepository productRepository,
                       StoreRepository storeRepository) {
        this.cartItemRepository = cartItemRepository;
        this.productRepository = productRepository;
        this.storeRepository = storeRepository;
    }

    public R list() {
        Long buyerId = UserContext.getUserId();
        LambdaQueryWrapper<CartItem> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(CartItem::getBuyerId, buyerId);
        wrapper.orderByDesc(CartItem::getCreatedAt);
        List<CartItem> items = cartItemRepository.selectList(wrapper);

        // Enrich with product info
        List<Map<String, Object>> result = new ArrayList<>();
        for (CartItem item : items) {
            Product product = productRepository.selectById(item.getProductId());
            if (product != null) {
                Map<String, Object> entry = new HashMap<>();
                entry.put("id", item.getId());
                entry.put("productId", product.getId());
                entry.put("title", product.getTitle());
                entry.put("price", product.getPrice());
                entry.put("images", product.getImages());
                entry.put("storeId", product.getStoreId());
                Store store = storeRepository.selectById(product.getStoreId());
                boolean ownProduct = store != null && Objects.equals(store.getUserId(), buyerId);
                entry.put("purchasable", !ownProduct && "published".equals(product.getStatus()));
                entry.put("unavailableReason", ownProduct ? "不能购买自己店铺的商品" :
                        ("published".equals(product.getStatus()) ? "" : "商品已下架"));
                entry.put("quantity", item.getQuantity());
                entry.put("createdAt", item.getCreatedAt());
                result.add(entry);
            }
        }
        return R.ok(result);
    }

    @Transactional
    public R add(Long productId, Integer quantity) {
        Long buyerId = UserContext.getUserId();
        Product product = productRepository.selectById(productId);
        if (product == null) {
            return R.error(BizCodeEnum.PRODUCT_NOT_FOUND);
        }
        if (!"published".equals(product.getStatus())) {
            return R.error(10031, "商品已下架，无法加入购物车");
        }
        Store store = storeRepository.selectById(product.getStoreId());
        if (store != null && Objects.equals(store.getUserId(), buyerId)) {
            return R.error(10092, "不能购买自己店铺的商品");
        }

        // Check if already in cart
        LambdaQueryWrapper<CartItem> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(CartItem::getBuyerId, buyerId);
        wrapper.eq(CartItem::getProductId, productId);
        CartItem existing = cartItemRepository.selectOne(wrapper);

        int qty = quantity != null && quantity > 0 ? quantity : 1;

        if (existing != null) {
            existing.setQuantity(existing.getQuantity() + qty);
            existing.setUpdatedAt(LocalDateTime.now());
            cartItemRepository.updateById(existing);
            return R.ok(existing);
        }

        CartItem item = new CartItem();
        item.setBuyerId(buyerId);
        item.setProductId(productId);
        item.setQuantity(qty);
        item.setCreatedAt(LocalDateTime.now());
        item.setUpdatedAt(LocalDateTime.now());
        cartItemRepository.insert(item);

        return R.ok(item);
    }

    @Transactional
    public R updateQuantity(Long cartItemId, Integer quantity) {
        Long buyerId = UserContext.getUserId();
        CartItem item = cartItemRepository.selectById(cartItemId);
        if (item == null || !item.getBuyerId().equals(buyerId)) {
            return R.error(10090, "cart item not found");
        }
        if (quantity <= 0) {
            cartItemRepository.deleteById(cartItemId);
            return R.ok("removed");
        }
        item.setQuantity(quantity);
        item.setUpdatedAt(LocalDateTime.now());
        cartItemRepository.updateById(item);
        return R.ok(item);
    }

    @Transactional
    public R remove(Long cartItemId) {
        Long buyerId = UserContext.getUserId();
        CartItem item = cartItemRepository.selectById(cartItemId);
        if (item == null || !item.getBuyerId().equals(buyerId)) {
            return R.error(10090, "cart item not found");
        }
        cartItemRepository.deleteById(cartItemId);
        return R.ok("removed");
    }

    @Transactional
    public R clear() {
        Long buyerId = UserContext.getUserId();
        LambdaQueryWrapper<CartItem> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(CartItem::getBuyerId, buyerId);
        cartItemRepository.delete(wrapper);
        return R.ok("cleared");
    }
}
