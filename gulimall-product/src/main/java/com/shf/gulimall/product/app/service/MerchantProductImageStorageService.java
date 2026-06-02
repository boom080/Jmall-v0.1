package com.shf.gulimall.product.app.service;

import com.aliyun.oss.OSS;
import com.aliyun.oss.OSSClientBuilder;
import com.shf.gulimall.product.app.dto.MerchantImageUploadResponse;
import com.shf.gulimall.product.config.MerchantOssProperties;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.io.InputStream;
import java.time.LocalDate;
import java.util.Locale;
import java.util.UUID;

@Service
public class MerchantProductImageStorageService {

    private static final long MAX_FILE_SIZE = 5L * 1024L * 1024L;

    private final MerchantOssProperties ossProperties;

    public MerchantProductImageStorageService(MerchantOssProperties ossProperties) {
        this.ossProperties = ossProperties;
    }

    public MerchantImageUploadResponse uploadProductImage(MultipartFile file) {
        validate(file);
        if (!ossProperties.isConfigured()) {
            throw new IllegalStateException("OSS 未配置。请先在根目录 .env.local 中填写 JRUNMALL_OSS_* 变量，未配置前仍可手动编辑图片 URL。");
        }

        String objectKey = buildObjectKey(file.getOriginalFilename());
        OSS client = new OSSClientBuilder().build(
                ossProperties.getEndpoint().trim(),
                ossProperties.getAccessKeyId().trim(),
                ossProperties.getAccessKeySecret().trim()
        );
        try (InputStream inputStream = file.getInputStream()) {
            client.putObject(ossProperties.getBucket().trim(), objectKey, inputStream);
        } catch (IOException ex) {
            throw new IllegalStateException("图片读取失败，无法上传到 OSS", ex);
        } finally {
            client.shutdown();
        }

        MerchantImageUploadResponse response = new MerchantImageUploadResponse();
        response.setObjectKey(objectKey);
        response.setUrl(buildPublicUrl(objectKey));
        return response;
    }

    private void validate(MultipartFile file) {
        if (file == null || file.isEmpty()) {
            throw new IllegalArgumentException("请选择一张图片后再上传");
        }
        if (file.getSize() > MAX_FILE_SIZE) {
            throw new IllegalArgumentException("图片大小不能超过 5MB");
        }
        String contentType = normalize(file.getContentType());
        if (!contentType.startsWith("image/")) {
            throw new IllegalArgumentException("仅支持上传图片文件");
        }
    }

    private String buildObjectKey(String originalFilename) {
        String prefix = normalize(ossProperties.getObjectPrefix());
        if (prefix.isEmpty()) {
            prefix = "merchant-products";
        }
        if (prefix.endsWith("/")) {
            prefix = prefix.substring(0, prefix.length() - 1);
        }
        LocalDate now = LocalDate.now();
        String extension = resolveExtension(originalFilename);
        return prefix + "/" + now.getYear() + "/" + now.getMonthValue() + "/" + now.getDayOfMonth()
                + "/" + UUID.randomUUID().toString().replace("-", "") + extension;
    }

    private String buildPublicUrl(String objectKey) {
        String baseUrl = normalize(ossProperties.getPublicBaseUrl());
        if (!baseUrl.isEmpty()) {
            return trimTrailingSlash(baseUrl) + "/" + objectKey;
        }

        String endpoint = normalize(ossProperties.getEndpoint());
        if (!endpoint.startsWith("http://") && !endpoint.startsWith("https://")) {
            endpoint = "https://" + endpoint;
        }
        String bucket = normalize(ossProperties.getBucket());
        return trimTrailingSlash(endpoint).replace("://", "://" + bucket + ".") + "/" + objectKey;
    }

    private String resolveExtension(String originalFilename) {
        String name = normalize(originalFilename);
        int index = name.lastIndexOf('.');
        if (index < 0) {
            return ".png";
        }
        String extension = name.substring(index).toLowerCase(Locale.ROOT);
        if (extension.length() > 10) {
            return ".png";
        }
        return extension;
    }

    private String normalize(String value) {
        return value == null ? "" : value.trim();
    }

    private String trimTrailingSlash(String value) {
        if (value.endsWith("/")) {
            return value.substring(0, value.length() - 1);
        }
        return value;
    }
}





