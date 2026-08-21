package com.jmall.controller;

import com.jmall.common.R;
import com.jmall.dto.ReviewRequest;
import com.jmall.service.ReviewService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/products/{productId}/reviews")
public class ReviewController {

    private final ReviewService reviewService;

    public ReviewController(ReviewService reviewService) {
        this.reviewService = reviewService;
    }

    @GetMapping
    public R list(@PathVariable Long productId) {
        return reviewService.listByProduct(productId);
    }

    @PostMapping
    public R create(@PathVariable Long productId, @Valid @RequestBody ReviewRequest request) {
        return reviewService.create(productId, request.getContent(), request.getRating());
    }
}
