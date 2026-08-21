package com.jmall.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("jmall_order")
public class Order {

    @TableId(type = IdType.AUTO)
    private Long id;

    private Long buyerId;
    private Long productId;
    private Long storeId;
    private Long amount;
    private Integer quantity;
    private String status;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
