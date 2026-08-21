package com.jmall.config;

import com.jmall.common.JwtUtil;
import com.jmall.common.LoginUser;
import com.jmall.common.UserContext;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;
import org.springframework.web.servlet.HandlerInterceptor;

@Component
public class LoginInterceptor implements HandlerInterceptor {

    private final JwtUtil jwtUtil;

    public LoginInterceptor(JwtUtil jwtUtil) {
        this.jwtUtil = jwtUtil;
    }

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) {
        String authHeader = request.getHeader("Authorization");

        if (!StringUtils.hasText(authHeader) || !authHeader.startsWith("Bearer ")) {
            // Allow GET/OPTIONS without auth for public browsing; write ops require token
            if ("GET".equalsIgnoreCase(request.getMethod())
                    || "OPTIONS".equalsIgnoreCase(request.getMethod())) {
                return true;
            }
            response.setStatus(401);
            return false;
        }

        String token = authHeader.substring(7);
        try {
            Long userId = jwtUtil.getUserIdFromToken(token);
            String username = jwtUtil.getUsernameFromToken(token);

            LoginUser loginUser = new LoginUser();
            loginUser.setUserId(userId);
            loginUser.setUsername(username);
            loginUser.setRole("user");
            UserContext.setUser(loginUser);

            return true;
        } catch (Exception e) {
            // Also allow GET with invalid/expired token — client can retry login
            if ("GET".equalsIgnoreCase(request.getMethod())
                    || "OPTIONS".equalsIgnoreCase(request.getMethod())) {
                return true;
            }
            response.setStatus(401);
            return false;
        }
    }

    @Override
    public void afterCompletion(HttpServletRequest request, HttpServletResponse response,
                                Object handler, Exception ex) {
        UserContext.remove();
    }
}
