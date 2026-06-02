package com.shf.gulimall.product.app.dto;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;

public class UserCartResponse {

    private Long userId;
    private String displayName;
    private Integer totalCount;
    private BigDecimal totalAmount;
    private List<UserCartItemResponse> items = new ArrayList<UserCartItemResponse>();

    public Long getUserId() {
        return userId;
    }

    public void setUserId(Long userId) {
        this.userId = userId;
    }

    public String getDisplayName() {
        return displayName;
    }

    public void setDisplayName(String displayName) {
        this.displayName = displayName;
    }

    public Integer getTotalCount() {
        return totalCount;
    }

    public void setTotalCount(Integer totalCount) {
        this.totalCount = totalCount;
    }

    public BigDecimal getTotalAmount() {
        return totalAmount;
    }

    public void setTotalAmount(BigDecimal totalAmount) {
        this.totalAmount = totalAmount;
    }

    public List<UserCartItemResponse> getItems() {
        return items;
    }

    public void setItems(List<UserCartItemResponse> items) {
        this.items = items;
    }
}





