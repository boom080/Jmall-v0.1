package com.jmall.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("jmall_transaction")
public class Transaction {

    @TableId(type = IdType.AUTO)
    private Long id;

    private Long buyerId;
    private Long productId;
    private Long storeId;
    private Long amount;
    private Integer multiplier;
    private Long goldEarned;
    private LocalDateTime createdAt;
}
