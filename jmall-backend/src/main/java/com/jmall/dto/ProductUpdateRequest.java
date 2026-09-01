package com.jmall.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.PositiveOrZero;
import jakarta.validation.constraints.Size;
import lombok.Data;

@Data
public class ProductUpdateRequest {
    @Size(max = 120)
    private String title;
    @Size(max = 160)
    private String subtitle;
    @Size(max = 64)
    private String category;
    private String description;
    @PositiveOrZero(message = "price must not be negative")
    private Long price;
    private String images;
    @NotBlank(message = "style is required")
    private String style;
    // AI-generated fields
    private String aiTitle;
    private String aiSellingPoints;
    private String aiDetail;
    private String aiStylePreviews;
    private String marketInsights;
    private String complianceResult;
    @Size(max = 10000)
    private String aiDraftMeta;
}
