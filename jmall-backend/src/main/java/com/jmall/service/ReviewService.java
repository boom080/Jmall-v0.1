package com.jmall.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.jmall.common.BizCodeEnum;
import com.jmall.common.R;
import com.jmall.common.UserContext;
import com.jmall.entity.Product;
import com.jmall.entity.Review;
import com.jmall.repository.ProductRepository;
import com.jmall.repository.ReviewRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;

@Service
public class ReviewService {

    private final ReviewRepository reviewRepository;
    private final ProductRepository productRepository;

    public ReviewService(ReviewRepository reviewRepository, ProductRepository productRepository) {
        this.reviewRepository = reviewRepository;
        this.productRepository = productRepository;
    }

    @Transactional
    public R create(Long productId, String content, Integer rating) {
        Long userId = UserContext.getUserId();

        // Check product exists
        Product product = productRepository.selectById(productId);
        if (product == null) {
            return R.error(BizCodeEnum.PRODUCT_NOT_FOUND);
        }

        Review review = new Review();
        review.setUserId(userId);
        review.setProductId(productId);
        review.setContent(content != null ? content : "");
        review.setRating(rating);
        review.setCreatedAt(LocalDateTime.now());
        reviewRepository.insert(review);

        return R.ok(review);
    }

    public R listByProduct(Long productId) {
        LambdaQueryWrapper<Review> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(Review::getProductId, productId)
               .orderByDesc(Review::getCreatedAt);

        List<Review> reviews = reviewRepository.selectList(wrapper);
        return R.ok(reviews);
    }
}
