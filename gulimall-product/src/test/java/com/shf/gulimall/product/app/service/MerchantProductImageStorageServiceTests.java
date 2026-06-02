package com.shf.gulimall.product.app.service;

import com.shf.gulimall.product.config.MerchantOssProperties;
import org.junit.Test;
import org.springframework.mock.web.MockMultipartFile;

import static org.junit.Assert.assertTrue;

public class MerchantProductImageStorageServiceTests {

    @Test(expected = IllegalArgumentException.class)
    public void rejectsNonImageFile() {
        MerchantOssProperties properties = new MerchantOssProperties();
        MerchantProductImageStorageService service = new MerchantProductImageStorageService(properties);
        MockMultipartFile file = new MockMultipartFile(
                "file",
                "demo.txt",
                "text/plain",
                "demo".getBytes()
        );
        service.uploadProductImage(file);
    }

    @Test
    public void returnsConfigurationErrorWhenOssIsNotConfigured() {
        MerchantOssProperties properties = new MerchantOssProperties();
        MerchantProductImageStorageService service = new MerchantProductImageStorageService(properties);
        MockMultipartFile file = new MockMultipartFile(
                "file",
                "demo.png",
                "image/png",
                "demo".getBytes()
        );

        try {
            service.uploadProductImage(file);
        } catch (IllegalStateException ex) {
            assertTrue(ex.getMessage().contains("OSS 未配置"));
            return;
        }
        throw new AssertionError("expected IllegalStateException");
    }
}





