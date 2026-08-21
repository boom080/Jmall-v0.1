package com.jmall.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("jmall_product")
public class Product {

    @TableId(type = IdType.AUTO)
    private Long id;

    private Long storeId;
    private String title;
    private String subtitle;
    private String category;
    private String description;
    private Long price;
    private String images;
    private String style;
    private String status;
    private Long viewCount;
    private Long likeCount;
    private Long saleCount;
    private String aiTitle;
    private String aiSellingPoints;
    private String aiDetail;
    private String aiStylePreviews;
    private String marketInsights;
    private String complianceResult;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
