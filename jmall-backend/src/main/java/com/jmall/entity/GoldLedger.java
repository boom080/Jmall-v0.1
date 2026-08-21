package com.jmall.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("jmall_gold_ledger")
public class GoldLedger {

    @TableId(type = IdType.AUTO)
    private Long id;

    private Long userId;
    private Long amount;
    private String type;
    private String description;
    private LocalDateTime createdAt;
}
