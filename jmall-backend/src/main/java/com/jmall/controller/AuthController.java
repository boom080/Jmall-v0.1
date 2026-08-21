package com.jmall.controller;

import com.jmall.common.R;
import com.jmall.dto.LoginRequest;
import com.jmall.dto.RegisterRequest;
import com.jmall.service.AuthService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/auth")
public class AuthController {

    private final AuthService authService;

    public AuthController(AuthService authService) {
        this.authService = authService;
    }

    @PostMapping("/register")
    public R register(@Valid @RequestBody RegisterRequest request) {
        return authService.register(request.getUsername(), request.getPassword(), request.getNickname());
    }

    @PostMapping("/login")
    public R login(@Valid @RequestBody LoginRequest request) {
        return authService.login(request.getUsername(), request.getPassword());
    }

    @GetMapping("/me")
    public R me() {
        return authService.getCurrentUser();
    }

    @PostMapping("/logout")
    public R logout() {
        return R.ok("logged out");
    }
}
