package com.jmall.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("jmall_store")
public class Store {

    @TableId(type = IdType.AUTO)
    private Long id;

    private Long userId;
    private String name;
    private String category;
    private String description;
    private String decorationConfig;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
