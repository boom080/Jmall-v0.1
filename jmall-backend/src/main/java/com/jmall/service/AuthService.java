package com.jmall.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.jmall.common.*;
import com.jmall.entity.Store;
import com.jmall.entity.User;
import com.jmall.repository.StoreRepository;
import com.jmall.repository.UserRepository;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;

@Service
public class AuthService {

    private final UserRepository userRepository;
    private final StoreRepository storeRepository;
    private final JwtUtil jwtUtil;
    private final BCryptPasswordEncoder passwordEncoder;

    public AuthService(UserRepository userRepository, StoreRepository storeRepository, JwtUtil jwtUtil) {
        this.userRepository = userRepository;
        this.storeRepository = storeRepository;
        this.jwtUtil = jwtUtil;
        this.passwordEncoder = new BCryptPasswordEncoder();
    }

    @Transactional
    public R register(String username, String password, String nickname) {
        // Check duplicate username
        LambdaQueryWrapper<User> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(User::getUsername, username);
        if (userRepository.selectCount(wrapper) > 0) {
            return R.error(BizCodeEnum.DUPLICATE_USERNAME);
        }

        User user = new User();
        user.setUsername(username);
        user.setPasswordHash(passwordEncoder.encode(password));
        user.setNickname(nickname);
        user.setRole("user");
        user.setGoldBalance(50000L);  // 1 gold = 1 yuan
        user.setPointsBalance(0L);
        user.setCheckinStreak(0);
        user.setCreatedAt(LocalDateTime.now());
        user.setUpdatedAt(LocalDateTime.now());
        userRepository.insert(user);

        // Auto-create a store for the new user
        Store store = new Store();
        store.setUserId(user.getId());
        store.setName((nickname != null && !nickname.isEmpty() ? nickname : username) + "的店铺");
        store.setCategory("其他");
        store.setDescription("欢迎光临！");
        store.setCreatedAt(LocalDateTime.now());
        store.setUpdatedAt(LocalDateTime.now());
        storeRepository.insert(store);

        // Link store to user
        user.setStoreId(store.getId());
        user.setUpdatedAt(LocalDateTime.now());
        userRepository.updateById(user);

        return R.ok("registration successful");
    }

    public R login(String username, String password) {
        LambdaQueryWrapper<User> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(User::getUsername, username);
        User user = userRepository.selectOne(wrapper);

        if (user == null || !passwordEncoder.matches(password, user.getPasswordHash())) {
            return R.error(BizCodeEnum.INVALID_CREDENTIALS);
        }

        String token = jwtUtil.generateToken(user.getId(), user.getUsername());

        // Return token + user info (without sensitive fields)
        java.util.Map<String, Object> result = new java.util.LinkedHashMap<>();
        result.put("token", token);
        result.put("user", toUserDto(user));
        return R.ok(result);
    }

    private java.util.Map<String, Object> toUserDto(User user) {
        java.util.Map<String, Object> dto = new java.util.LinkedHashMap<>();
        dto.put("id", user.getId());
        dto.put("username", user.getUsername());
        dto.put("nickname", user.getNickname());
        dto.put("avatar", user.getAvatar());
        dto.put("role", user.getRole());
        dto.put("goldBalance", user.getGoldBalance());
        dto.put("storeId", user.getStoreId());
        return dto;
    }

    public R getCurrentUser() {
        Long userId = UserContext.getUserId();
        if (userId == null) {
            return R.error(BizCodeEnum.AUTH_ERROR);
        }
        User user = userRepository.selectById(userId);
        if (user == null) {
            return R.error(BizCodeEnum.USER_NOT_FOUND);
        }
        return R.ok(user);
    }
}
