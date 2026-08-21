package com.jmall.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Data;

@Data
public class RegisterRequest {
    @NotBlank(message = "username is required")
    @Size(min = 3, max = 64, message = "username must be 3-64 chars")
    private String username;
    @NotBlank(message = "password is required")
    @Size(min = 6, max = 64, message = "password must be 6-64 chars")
    private String password;
    @NotBlank(message = "nickname is required")
    @Size(max = 64, message = "nickname max 64 chars")
    private String nickname;
}
