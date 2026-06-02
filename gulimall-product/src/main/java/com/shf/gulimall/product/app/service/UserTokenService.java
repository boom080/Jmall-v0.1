package com.shf.gulimall.product.app.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.shf.gulimall.product.app.dto.CurrentUserProfile;
import com.shf.gulimall.product.config.UserAuthTokenProperties;
import org.springframework.stereotype.Service;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.Base64;
import java.util.LinkedHashMap;
import java.util.Map;

@Service
public class UserTokenService {

    private final UserAuthTokenProperties properties;
    private final ObjectMapper objectMapper = new ObjectMapper();

    public UserTokenService(UserAuthTokenProperties properties) {
        this.properties = properties;
    }

    public String generateToken(CurrentUserProfile profile) {
        try {
            Map<String, Object> payload = new LinkedHashMap<String, Object>();
            payload.put("userId", profile.getUserId());
            payload.put("username", profile.getUsername());
            payload.put("displayName", profile.getDisplayName());
            payload.put("exp", Instant.now().plusSeconds(properties.getTtlHours() * 3600).getEpochSecond());
            String payloadJson = objectMapper.writeValueAsString(payload);
            String payloadBase64 = Base64.getUrlEncoder().withoutPadding()
                    .encodeToString(payloadJson.getBytes(StandardCharsets.UTF_8));
            String signature = sign(payloadBase64);
            return payloadBase64 + "." + signature;
        } catch (Exception ex) {
            throw new IllegalStateException("生成登录 token 失败", ex);
        }
    }

    public CurrentUserProfile parseToken(String token) {
        try {
            if (token == null || token.trim().isEmpty() || !token.contains(".")) {
                return null;
            }
            String[] parts = token.trim().split("\\.");
            if (parts.length != 2) {
                return null;
            }
            String payloadBase64 = parts[0];
            String signature = parts[1];
            if (!sign(payloadBase64).equals(signature)) {
                return null;
            }
            String payloadJson = new String(Base64.getUrlDecoder().decode(payloadBase64), StandardCharsets.UTF_8);
            Map<?, ?> payload = objectMapper.readValue(payloadJson, Map.class);
            Number exp = (Number) payload.get("exp");
            if (exp == null || exp.longValue() < Instant.now().getEpochSecond()) {
                return null;
            }
            CurrentUserProfile profile = new CurrentUserProfile();
            profile.setUserId(payload.get("userId") == null ? null : Long.valueOf(String.valueOf(payload.get("userId"))));
            profile.setUsername(payload.get("username") == null ? null : String.valueOf(payload.get("username")));
            profile.setDisplayName(payload.get("displayName") == null ? profile.getUsername() : String.valueOf(payload.get("displayName")));
            return profile;
        } catch (Exception ex) {
            return null;
        }
    }

    private String sign(String payloadBase64) throws Exception {
        Mac mac = Mac.getInstance("HmacSHA256");
        mac.init(new SecretKeySpec(properties.getSecret().getBytes(StandardCharsets.UTF_8), "HmacSHA256"));
        byte[] signed = mac.doFinal(payloadBase64.getBytes(StandardCharsets.UTF_8));
        return Base64.getUrlEncoder().withoutPadding().encodeToString(signed);
    }
}





