package com.shf.gulimall.product.app.dto;

import java.util.Date;

public class SeckillOrderEvent {

    private String requestId;
    private Long userId;
    private Long skuId;
    private Integer quantity;
    private String seckillSessionId;
    private String orderToken;
    private Date timestamp;

    public String getRequestId() {
        return requestId;
    }

    public void setRequestId(String requestId) {
        this.requestId = requestId;
    }

    public Long getUserId() {
        return userId;
    }

    public void setUserId(Long userId) {
        this.userId = userId;
    }

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

    public String getSeckillSessionId() {
        return seckillSessionId;
    }

    public void setSeckillSessionId(String seckillSessionId) {
        this.seckillSessionId = seckillSessionId;
    }

    public String getOrderToken() {
        return orderToken;
    }

    public void setOrderToken(String orderToken) {
        this.orderToken = orderToken;
    }

    public Date getTimestamp() {
        return timestamp;
    }

    public void setTimestamp(Date timestamp) {
        this.timestamp = timestamp;
    }
}





