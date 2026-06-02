package com.shf.gulimall.product.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@Component("siteUrlProperties")
@ConfigurationProperties(prefix = "jrunmall.site")
public class SiteUrlProperties {

    private String mainBaseUrl = "http://jrunmall.localhost";
    private String authBaseUrl = "http://auth.jrunmall.localhost";
    private String memberBaseUrl = "http://member.jrunmall.localhost";
    private String cartBaseUrl = "http://cart.jrunmall.localhost";
    private String searchBaseUrl = "http://search.jrunmall.localhost";
    private String itemBaseUrl = "http://item.jrunmall.localhost";
    private String seckillBaseUrl = "http://seckill.jrunmall.localhost";
    private String cookieDomain = "";

    public String getHomeUrl() {
        return mainBaseUrl + "/";
    }

    public String getLoginUrl() {
        return authBaseUrl + "/login.html";
    }

    public String getRegisterUrl() {
        return authBaseUrl + "/reg.html";
    }

    public String getLogoutUrl() {
        return authBaseUrl + "/loguot.html";
    }

    public String getMemberOrderUrl() {
        return memberBaseUrl + "/memberOrder.html";
    }

    public String getCartUrl() {
        return cartBaseUrl + "/cart.html";
    }

    public String getCartAddItemUrl() {
        return cartBaseUrl + "/addCartItem";
    }

    public String getSearchListUrl() {
        return searchBaseUrl + "/list.html";
    }

    public String getCurrentSeckillSkusUrl() {
        return seckillBaseUrl + "/getCurrentSeckillSkus";
    }

    public String getKillUrl() {
        return seckillBaseUrl + "/kill";
    }

    public String getMainBaseUrl() {
        return mainBaseUrl;
    }

    public void setMainBaseUrl(String mainBaseUrl) {
        this.mainBaseUrl = mainBaseUrl;
    }

    public String getAuthBaseUrl() {
        return authBaseUrl;
    }

    public void setAuthBaseUrl(String authBaseUrl) {
        this.authBaseUrl = authBaseUrl;
    }

    public String getMemberBaseUrl() {
        return memberBaseUrl;
    }

    public void setMemberBaseUrl(String memberBaseUrl) {
        this.memberBaseUrl = memberBaseUrl;
    }

    public String getCartBaseUrl() {
        return cartBaseUrl;
    }

    public void setCartBaseUrl(String cartBaseUrl) {
        this.cartBaseUrl = cartBaseUrl;
    }

    public String getSearchBaseUrl() {
        return searchBaseUrl;
    }

    public void setSearchBaseUrl(String searchBaseUrl) {
        this.searchBaseUrl = searchBaseUrl;
    }

    public String getItemBaseUrl() {
        return itemBaseUrl;
    }

    public void setItemBaseUrl(String itemBaseUrl) {
        this.itemBaseUrl = itemBaseUrl;
    }

    public String getSeckillBaseUrl() {
        return seckillBaseUrl;
    }

    public void setSeckillBaseUrl(String seckillBaseUrl) {
        this.seckillBaseUrl = seckillBaseUrl;
    }

    public String getCookieDomain() {
        return cookieDomain;
    }

    public void setCookieDomain(String cookieDomain) {
        this.cookieDomain = cookieDomain;
    }
}





