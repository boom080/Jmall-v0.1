package com.shf.gulimall.product.app.dto;

public class UserCartItemUpsertRequest {

    private Long skuId;
    private Integer quantity = 1;

    public Long getSkuId() {
        return skuId;
    }

    public void setSkuId(Long skuId) {
        this.skuId = skuId;
    }

    public Integer getQuantity() {
        return quantity;
    }

    public void setQuantity(Integer quantity) {
        this.quantity = quantity;
    }
}





