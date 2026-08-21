package com.jmall.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;
import jakarta.validation.constraints.Size;
import lombok.Data;

@Data
public class ProductUpdateRequest {
    @NotBlank(message = "title is required")
    @Size(max = 120)
    private String title;
    @Size(max = 160)
    private String subtitle;
    @NotBlank(message = "category is required")
    @Size(max = 64)
    private String category;
    private String description;
    @NotNull(message = "price is required")
    @Positive(message = "price must be greater than 0")
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
}
