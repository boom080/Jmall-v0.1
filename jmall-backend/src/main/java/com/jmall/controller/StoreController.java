package com.jmall.controller;

import com.jmall.common.R;
import com.jmall.dto.StoreCreateRequest;
import com.jmall.service.StoreService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/stores")
public class StoreController {

    private final StoreService storeService;

    public StoreController(StoreService storeService) {
        this.storeService = storeService;
    }

    @PostMapping
    public R create(@Valid @RequestBody StoreCreateRequest request) {
        return storeService.create(request);
    }

    @GetMapping("/mine")
    public R getMyStore() {
        return storeService.getMyStore();
    }

    @GetMapping("/mine/stats")
    public R getMyStats() {
        return storeService.getMyStats();
    }

    @GetMapping("/{id}")
    public R getById(@PathVariable Long id) {
        return storeService.getById(id);
    }

    @GetMapping("/{id}/stats")
    public R getStats(@PathVariable Long id) {
        return storeService.getStats(id);
    }

    @PutMapping("/{id}")
    public R update(@PathVariable Long id, @Valid @RequestBody StoreCreateRequest request) {
        return storeService.update(id, request);
    }

    @GetMapping("/{id}/decoration")
    public R getDecoration(@PathVariable Long id) {
        return storeService.getDecoration(id);
    }

    @GetMapping
    public R list() {
        return storeService.list();
    }
}
