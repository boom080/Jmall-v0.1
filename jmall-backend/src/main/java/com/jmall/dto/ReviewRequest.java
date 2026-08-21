package com.jmall.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.Data;

@Data
public class ReviewRequest {
    @NotNull(message = "productId is required")
    private Long productId;
    @Size(max = 500)
    private String content;
    @NotNull(message = "rating is required")
    @Min(1) @Max(5)
    private Integer rating;
}
