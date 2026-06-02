package com.shf.gulimall.product.app.dto;

public class UserOrderCreateRequest {

    private String note = "";
    private Long addressId;

    public String getNote() {
        return note;
    }

    public void setNote(String note) {
        this.note = note;
    }

    public Long getAddressId() {
        return addressId;
    }

    public void setAddressId(Long addressId) {
        this.addressId = addressId;
    }
}





