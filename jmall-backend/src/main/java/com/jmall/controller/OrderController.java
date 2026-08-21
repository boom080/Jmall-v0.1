package com.jmall.controller;

import com.jmall.common.R;
import com.jmall.service.OrderService;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/orders")
public class OrderController {

    private final OrderService orderService;

    public OrderController(OrderService orderService) {
        this.orderService = orderService;
    }

    @PostMapping("/checkout")
    public R checkout() {
        return orderService.createFromCart();
    }

    @GetMapping
    public R list() {
        return orderService.list();
    }
}
