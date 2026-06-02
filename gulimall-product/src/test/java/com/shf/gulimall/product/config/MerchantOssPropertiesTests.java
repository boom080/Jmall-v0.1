package com.shf.gulimall.product.config;

import org.junit.Test;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

public class MerchantOssPropertiesTests {

    @Test
    public void returnsFalseWhenRequiredFieldsMissing() {
        MerchantOssProperties properties = new MerchantOssProperties();
        properties.setEndpoint("https://oss-example.aliyuncs.com");
        properties.setBucket("demo-bucket");
        assertFalse(properties.isConfigured());
    }

    @Test
    public void returnsTrueWhenRequiredFieldsPresent() {
        MerchantOssProperties properties = new MerchantOssProperties();
        properties.setEndpoint("https://oss-example.aliyuncs.com");
        properties.setBucket("demo-bucket");
        properties.setAccessKeyId("key");
        properties.setAccessKeySecret("secret");
        assertTrue(properties.isConfigured());
    }
}





