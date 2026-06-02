package com.shf.gulimall.product.app.dto;

public class UserAuthLoginResponse {

    private String token;
    private CurrentUserProfile user;

    public String getToken() {
        return token;
    }

    public void setToken(String token) {
        this.token = token;
    }

    public CurrentUserProfile getUser() {
        return user;
    }

    public void setUser(CurrentUserProfile user) {
        this.user = user;
    }
}





