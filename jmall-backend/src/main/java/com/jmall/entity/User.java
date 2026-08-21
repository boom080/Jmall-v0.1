package com.jmall.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDate;
import java.time.LocalDateTime;

@Data
@TableName("jmall_user")
public class User {

    @TableId(type = IdType.AUTO)
    private Long id;

    private String username;
    private String passwordHash;
    private String nickname;
    private String avatar;
    private String role;
    private Long goldBalance;
    private Long pointsBalance;
    private Integer checkinStreak;
    private LocalDate lastCheckin;
    private Long storeId;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
