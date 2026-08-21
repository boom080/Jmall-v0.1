package com.jmall.dto;

import jakarta.validation.constraints.NotNull;
import lombok.Data;

@Data
public class PurchaseRequest {
    @NotNull(message = "productId is required")
    private Long productId;
}
