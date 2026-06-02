package com.shf.gulimall.product.app.dto;

import java.util.ArrayList;
import java.util.List;

public class UserCatalogProductPageResponse {

    private List<UserCatalogProductCardResponse> items = new ArrayList<>();
    private int totalCount;
    private int pageSize;
    private int currentPage;
    private int totalPage;

    public List<UserCatalogProductCardResponse> getItems() {
        return items;
    }

    public void setItems(List<UserCatalogProductCardResponse> items) {
        this.items = items;
    }

    public int getTotalCount() {
        return totalCount;
    }

    public void setTotalCount(int totalCount) {
        this.totalCount = totalCount;
    }

    public int getPageSize() {
        return pageSize;
    }

    public void setPageSize(int pageSize) {
        this.pageSize = pageSize;
    }

    public int getCurrentPage() {
        return currentPage;
    }

    public void setCurrentPage(int currentPage) {
        this.currentPage = currentPage;
    }

    public int getTotalPage() {
        return totalPage;
    }

    public void setTotalPage(int totalPage) {
        this.totalPage = totalPage;
    }
}





