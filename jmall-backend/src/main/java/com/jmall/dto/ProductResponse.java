package com.jmall.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ProductResponse {
    private Long id;
    private Long storeId;
    private String storeName;
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
    private Boolean purchasable;
    private String unavailableReason;
    private String aiTitle;
    private String aiSellingPoints;
    private String aiDetail;
    private String aiStylePreviews;
    private String marketInsights;
    private String complianceResult;
    private String aiDraftMeta;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
