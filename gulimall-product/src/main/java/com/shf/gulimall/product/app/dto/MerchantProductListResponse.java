package com.shf.gulimall.product.app.dto;

import java.util.ArrayList;
import java.util.List;

public class MerchantProductListResponse {

    private List<MerchantProductResponse> items = new ArrayList<MerchantProductResponse>();

    public List<MerchantProductResponse> getItems() {
        return items;
    }

    public void setItems(List<MerchantProductResponse> items) {
        this.items = items;
    }
}





