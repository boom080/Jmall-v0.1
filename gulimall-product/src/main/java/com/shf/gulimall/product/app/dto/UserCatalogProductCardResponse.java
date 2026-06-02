package com.shf.gulimall.product.app.dto;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;

public class UserCatalogProductCardResponse {

    private Long id;
    private String title;
    private String category;
    private String subtitle;
    private List<String> sellingPoints = new ArrayList<>();
    private BigDecimal price;
    private String coverUrl;
    private String summary;

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getTitle() {
        return title;
    }

    public void setTitle(String title) {
        this.title = title;
    }

    public String getCategory() {
        return category;
    }

    public void setCategory(String category) {
        this.category = category;
    }

    public String getSubtitle() {
        return subtitle;
    }

    public void setSubtitle(String subtitle) {
        this.subtitle = subtitle;
    }

    public List<String> getSellingPoints() {
        return sellingPoints;
    }

    public void setSellingPoints(List<String> sellingPoints) {
        this.sellingPoints = sellingPoints;
    }

    public BigDecimal getPrice() {
        return price;
    }

    public void setPrice(BigDecimal price) {
        this.price = price;
    }

    public String getCoverUrl() {
        return coverUrl;
    }

    public void setCoverUrl(String coverUrl) {
        this.coverUrl = coverUrl;
    }

    public String getSummary() {
        return summary;
    }

    public void setSummary(String summary) {
        this.summary = summary;
    }
}





