package com.jmall.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Data;

@Data
public class StoreCreateRequest {
    @NotBlank(message = "store name is required")
    @Size(max = 120)
    private String name;
    @NotBlank(message = "category is required")
    @Size(max = 64)
    private String category;
    private String description;
    private String decorationConfig;
}
