package com.jmall.controller;

import com.jmall.common.R;
import com.jmall.service.UserService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/user")
public class UserController {

    private final UserService userService;

    public UserController(UserService userService) {
        this.userService = userService;
    }

    @GetMapping("/profile")
    public R profile() {
        return userService.getProfile();
    }

    @GetMapping("/gold")
    public R gold() {
        return userService.getGoldBalance();
    }

    @GetMapping("/gold-ledger")
    public R goldLedger() {
        return userService.getGoldLedger();
    }
}
