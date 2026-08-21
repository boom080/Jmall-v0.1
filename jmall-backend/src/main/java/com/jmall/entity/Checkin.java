package com.jmall.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDate;
import java.time.LocalDateTime;

@Data
@TableName("jmall_checkin")
public class Checkin {

    @TableId(type = IdType.AUTO)
    private Long id;

    private Long userId;
    private LocalDate checkinDate;
    private Long goldReward;
    private Integer streakDay;
    private LocalDateTime createdAt;
}
