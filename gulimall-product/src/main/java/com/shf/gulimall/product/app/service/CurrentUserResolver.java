package com.shf.gulimall.product.app.service;

import com.shf.gulimall.product.app.dto.CurrentUserProfile;
import org.springframework.stereotype.Component;
import org.springframework.web.context.request.RequestAttributes;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;

import javax.servlet.http.HttpServletRequest;

@Component
public class CurrentUserResolver {

    private final UserTokenService userTokenService;

    public CurrentUserResolver(UserTokenService userTokenService) {
        this.userTokenService = userTokenService;
    }

    public CurrentUserProfile requireCurrentUser() {
        CurrentUserProfile user = getCurrentUser();
        if (user == null || user.getUserId() == null) {
            throw new IllegalStateException("请先登录");
        }
        return user;
    }

    public CurrentUserProfile getCurrentUser() {
        RequestAttributes attributes = RequestContextHolder.getRequestAttributes();
        if (!(attributes instanceof ServletRequestAttributes)) {
            return null;
        }
        HttpServletRequest request = ((ServletRequestAttributes) attributes).getRequest();
        if (request == null) {
            return null;
        }
        String authorization = request.getHeader("Authorization");
        if (authorization == null || authorization.trim().isEmpty()) {
            return null;
        }
        String trimmedAuthorization = authorization.trim();
        String token = trimmedAuthorization.regionMatches(true, 0, "Bearer ", 0, 7)
                ? trimmedAuthorization.substring(7).trim()
                : trimmedAuthorization;
        return userTokenService.parseToken(token);
    }
}





