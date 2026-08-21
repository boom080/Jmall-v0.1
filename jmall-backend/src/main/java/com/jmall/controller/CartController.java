package com.jmall.controller;

import com.jmall.common.R;
import com.jmall.service.CartService;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/cart")
public class CartController {

    private final CartService cartService;

    public CartController(CartService cartService) {
        this.cartService = cartService;
    }

    @GetMapping
    public R list() {
        return cartService.list();
    }

    @PostMapping
    public R add(@RequestBody Map<String, Object> body) {
        Long productId = Long.valueOf(body.get("productId").toString());
        Integer quantity = body.containsKey("quantity") ? Integer.valueOf(body.get("quantity").toString()) : 1;
        return cartService.add(productId, quantity);
    }

    @PutMapping("/{id}/quantity")
    public R updateQuantity(@PathVariable Long id, @RequestBody Map<String, Integer> body) {
        return cartService.updateQuantity(id, body.get("quantity"));
    }

    @DeleteMapping("/{id}")
    public R remove(@PathVariable Long id) {
        return cartService.remove(id);
    }

    @DeleteMapping("/clear")
    public R clear() {
        return cartService.clear();
    }
}
