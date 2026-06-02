package com.shf.gulimall.product.app;

import com.shf.common.utils.R;
import com.shf.gulimall.product.app.dto.UserAuthLoginRequest;
import com.shf.gulimall.product.app.dto.UserAuthRegisterRequest;
import com.shf.gulimall.product.app.service.UserAuthApplicationService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("user/auth")
public class UserAuthController {

    private final UserAuthApplicationService userAuthApplicationService;

    public UserAuthController(UserAuthApplicationService userAuthApplicationService) {
        this.userAuthApplicationService = userAuthApplicationService;
    }

    @PostMapping("/register")
    public R register(@RequestBody UserAuthRegisterRequest request) {
        try {
            userAuthApplicationService.register(request);
            return R.ok().put("message", "注册成功");
        } catch (IllegalArgumentException ex) {
            return R.error(400, ex.getMessage());
        }
    }

    @PostMapping("/login")
    public R login(@RequestBody UserAuthLoginRequest request) {
        try {
            return R.ok().setData(userAuthApplicationService.login(request));
        } catch (IllegalArgumentException ex) {
            return R.error(400, ex.getMessage());
        }
    }

    @PostMapping("/logout")
    public R logout() {
        return R.ok().put("message", "已退出登录");
    }

    @GetMapping("/me")
    public R me() {
        try {
            return R.ok().setData(userAuthApplicationService.me());
        } catch (IllegalStateException ex) {
            return R.error(401, ex.getMessage());
        }
    }
}





