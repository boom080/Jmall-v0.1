package com.shf.gulimall.product.app.service;

import com.shf.common.utils.R;
import com.shf.gulimall.product.app.dto.CurrentUserProfile;
import com.shf.gulimall.product.app.dto.UserAuthLoginRequest;
import com.shf.gulimall.product.app.dto.UserAuthLoginResponse;
import com.shf.gulimall.product.app.dto.UserAuthRegisterRequest;
import com.shf.gulimall.product.feign.MemberUserFeignService;
import org.springframework.stereotype.Service;

import java.util.Map;

@Service
public class UserAuthApplicationService {

    private final MemberUserFeignService memberUserFeignService;
    private final UserTokenService userTokenService;
    private final CurrentUserResolver currentUserResolver;

    public UserAuthApplicationService(MemberUserFeignService memberUserFeignService,
                                      UserTokenService userTokenService,
                                      CurrentUserResolver currentUserResolver) {
        this.memberUserFeignService = memberUserFeignService;
        this.userTokenService = userTokenService;
        this.currentUserResolver = currentUserResolver;
    }

    public void register(UserAuthRegisterRequest request) {
        validateRegisterRequest(request);
        R response = memberUserFeignService.register(request);
        if (response.get("code") instanceof Number && ((Number) response.get("code")).intValue() != 0) {
            throw new IllegalArgumentException(String.valueOf(response.get("msg")));
        }
    }

    public UserAuthLoginResponse login(UserAuthLoginRequest request) {
        validateLoginRequest(request);
        R response = memberUserFeignService.login(request);
        if (response.get("code") instanceof Number && ((Number) response.get("code")).intValue() != 0) {
            throw new IllegalArgumentException(String.valueOf(response.get("msg")));
        }
        Object data = response.get("data");
        if (!(data instanceof Map)) {
            throw new IllegalArgumentException("登录失败");
        }
        Map<?, ?> member = (Map<?, ?>) data;
        CurrentUserProfile profile = new CurrentUserProfile();
        profile.setUserId(Long.valueOf(String.valueOf(member.get("id"))));
        profile.setUsername(String.valueOf(member.get("username")));
        Object nickname = member.get("nickname");
        profile.setDisplayName(nickname == null || String.valueOf(nickname).trim().isEmpty()
                ? profile.getUsername()
                : String.valueOf(nickname));

        UserAuthLoginResponse loginResponse = new UserAuthLoginResponse();
        loginResponse.setUser(profile);
        loginResponse.setToken(userTokenService.generateToken(profile));
        return loginResponse;
    }

    public CurrentUserProfile me() {
        return currentUserResolver.requireCurrentUser();
    }

    private void validateRegisterRequest(UserAuthRegisterRequest request) {
        if (request == null) {
            throw new IllegalArgumentException("注册请求不能为空");
        }
        if (request.getUserName() == null || request.getUserName().trim().isEmpty()) {
            throw new IllegalArgumentException("用户名不能为空");
        }
        if (request.getPhone() == null || request.getPhone().trim().isEmpty()) {
            throw new IllegalArgumentException("手机号不能为空");
        }
        if (request.getPassword() == null || request.getPassword().trim().length() < 6) {
            throw new IllegalArgumentException("密码至少 6 位");
        }
    }

    private void validateLoginRequest(UserAuthLoginRequest request) {
        if (request == null) {
            throw new IllegalArgumentException("登录请求不能为空");
        }
        if (request.getLoginacct() == null || request.getLoginacct().trim().isEmpty()) {
            throw new IllegalArgumentException("账号不能为空");
        }
        if (request.getPassword() == null || request.getPassword().trim().isEmpty()) {
            throw new IllegalArgumentException("密码不能为空");
        }
    }
}





