package com.jmall.controller;

import com.jmall.common.R;
import com.jmall.service.CollectionService;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/collections")
public class CollectionController {

    private final CollectionService collectionService;

    public CollectionController(CollectionService collectionService) {
        this.collectionService = collectionService;
    }

    @GetMapping
    public R list() {
        return collectionService.list();
    }

    @PostMapping("/{productId}")
    public R add(@PathVariable Long productId) {
        return collectionService.add(productId);
    }

    @DeleteMapping("/{productId}")
    public R remove(@PathVariable Long productId) {
        return collectionService.remove(productId);
    }

    @GetMapping("/check/{productId}")
    public R check(@PathVariable Long productId) {
        return collectionService.isCollected(productId);
    }
}
