package com.jmall.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class UserProfileResponse {
    private Long id;
    private String username;
    private String nickname;
    private Long goldBalance;
    private Long pointsBalance;
    private Integer checkinStreak;
    private String role;
}
