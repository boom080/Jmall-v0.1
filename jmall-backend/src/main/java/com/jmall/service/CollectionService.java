package com.jmall.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.jmall.common.BizCodeEnum;
import com.jmall.common.R;
import com.jmall.common.UserContext;
import com.jmall.entity.Product;
import com.jmall.entity.UserCollection;
import com.jmall.repository.ProductRepository;
import com.jmall.repository.UserCollectionRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

@Service
public class CollectionService {

    private final UserCollectionRepository collectionRepository;
    private final ProductRepository productRepository;
    private final AchievementService achievementService;

    public CollectionService(UserCollectionRepository collectionRepository,
                             ProductRepository productRepository,
                             AchievementService achievementService) {
        this.collectionRepository = collectionRepository;
        this.productRepository = productRepository;
        this.achievementService = achievementService;
    }

    @Transactional
    public R add(Long productId) {
        Long userId = UserContext.getUserId();

        // Check product exists
        Product product = productRepository.selectById(productId);
        if (product == null) {
            return R.error(BizCodeEnum.PRODUCT_NOT_FOUND);
        }

        // Check if already collected
        LambdaQueryWrapper<UserCollection> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(UserCollection::getUserId, userId)
               .eq(UserCollection::getProductId, productId);
        if (collectionRepository.selectCount(wrapper) > 0) {
            return R.error(10091, "already collected");
        }

        UserCollection collection = new UserCollection();
        collection.setUserId(userId);
        collection.setProductId(productId);
        collection.setCreatedAt(LocalDateTime.now());
        collectionRepository.insert(collection);

        product.setLikeCount((product.getLikeCount() == null ? 0L : product.getLikeCount()) + 1);
        product.setUpdatedAt(LocalDateTime.now());
        productRepository.updateById(product);

        // Check achievement unlocks (e.g. COLLECTOR_10)
        achievementService.checkAndUnlock(userId);

        return R.ok("collected");
    }

    @Transactional
    public R remove(Long productId) {
        Long userId = UserContext.getUserId();

        LambdaQueryWrapper<UserCollection> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(UserCollection::getUserId, userId)
               .eq(UserCollection::getProductId, productId);
        long removed = collectionRepository.delete(wrapper);
        if (removed > 0) {
            Product product = productRepository.selectById(productId);
            if (product != null) {
                product.setLikeCount(Math.max(0L,
                        (product.getLikeCount() == null ? 0L : product.getLikeCount()) - removed));
                product.setUpdatedAt(LocalDateTime.now());
                productRepository.updateById(product);
            }
        }

        return R.ok("removed");
    }

    public R list() {
        Long userId = UserContext.getUserId();

        LambdaQueryWrapper<UserCollection> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(UserCollection::getUserId, userId)
               .orderByDesc(UserCollection::getCreatedAt);

        List<UserCollection> collections = collectionRepository.selectList(wrapper);
        List<Product> products = new ArrayList<>();
        for (UserCollection uc : collections) {
            Product product = productRepository.selectById(uc.getProductId());
            if (product != null) {
                products.add(product);
            }
        }

        return R.ok(products);
    }

    public R isCollected(Long productId) {
        Long userId = UserContext.getUserId();

        LambdaQueryWrapper<UserCollection> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(UserCollection::getUserId, userId)
               .eq(UserCollection::getProductId, productId);

        boolean collected = collectionRepository.selectCount(wrapper) > 0;
        return R.ok(collected);
    }
}
