package com.jmall.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class CheckinResponse {
    private Long goldReward;
    private Integer streakDay;
    private Long totalGold;
}
