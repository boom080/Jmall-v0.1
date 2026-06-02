package com.shf.gulimall.ai.adapter.client;

import com.shf.gulimall.ai.adapter.config.AiAdapterProperties;
import com.shf.gulimall.ai.adapter.model.AiModelOption;
import com.shf.gulimall.ai.adapter.model.KnowledgeBaseCreateRequest;
import com.shf.gulimall.ai.adapter.model.KnowledgeBaseCreateResponse;
import com.shf.gulimall.ai.adapter.model.KnowledgeBaseDocument;
import com.shf.gulimall.ai.adapter.model.KnowledgeBaseDocumentTextRequest;
import com.shf.gulimall.ai.adapter.model.KnowledgeBaseOption;
import com.shf.gulimall.ai.adapter.model.KnowledgeBaseUploadTxtResponse;
import com.shf.gulimall.ai.adapter.model.ProductCopyAiRequest;
import com.shf.gulimall.ai.adapter.model.ProductCopyAiResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestClientResponseException;
import org.springframework.web.client.RestTemplate;

import java.net.SocketTimeoutException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

public class AiHttpClient {

    private static final Logger log = LoggerFactory.getLogger(AiHttpClient.class);

    private final RestTemplate restTemplate;
    private final AiAdapterProperties properties;

    public AiHttpClient(RestTemplate restTemplate, AiAdapterProperties properties) {
        this.restTemplate = restTemplate;
        this.properties = properties;
    }

    public ProductCopyAiResponse generateProductCopy(ProductCopyAiRequest request) {
        if (!properties.isEnabled()) {
            return ProductCopyAiResponse.disabledFallback(request);
        }

        try {
            ProductCopyAiResponse response = restTemplate.postForObject(
                    properties.buildProductCopyUrl(),
                    request,
                    ProductCopyAiResponse.class
            );

            if (response == null) {
                log.warn("AI adapter received an empty response from {}", properties.buildProductCopyUrl());
                return ProductCopyAiResponse.failedFallback(request,
                        "java-empty-response-fallback",
                        "AI 服务返回空响应，已返回降级文案。");
            }

            return response.normalizeSuccess(request);
        } catch (ResourceAccessException ex) {
            log.warn("AI adapter resource access failure", ex);
            if (isTimeoutException(ex)) {
                return ProductCopyAiResponse.failedFallback(request,
                        "java-timeout-fallback",
                        "AI 服务调用超时，已返回降级文案。");
            }
            return ProductCopyAiResponse.failedFallback(request,
                    "java-resource-fallback",
                    "AI 服务暂时不可达，已返回降级文案。");
        } catch (RestClientResponseException ex) {
            log.warn("AI adapter remote service returned error status {}", ex.getRawStatusCode(), ex);
            return ProductCopyAiResponse.failedFallback(request,
                    "java-http-status-fallback",
                    "AI 服务响应异常(" + ex.getRawStatusCode() + ")，已返回降级文案。");
        } catch (RestClientException ex) {
            log.warn("AI adapter rest client failure", ex);
            return ProductCopyAiResponse.failedFallback(request,
                    "java-rest-fallback",
                    "AI 服务调用失败，已返回降级文案。");
        } catch (RuntimeException ex) {
            log.warn("AI adapter runtime failure", ex);
            return ProductCopyAiResponse.failedFallback(request,
                    "java-runtime-fallback",
                    "AI 服务处理异常，已返回降级文案。");
        }
    }

    public List<AiModelOption> getAvailableModels() {
        if (!properties.isEnabled()) {
            return buildFallbackModels();
        }

        try {
            AiModelOption[] response = restTemplate.getForObject(
                    properties.buildModelsUrl(),
                    AiModelOption[].class
            );
            if (response == null || response.length == 0) {
                return buildFallbackModels();
            }
            return Arrays.asList(response);
        } catch (RestClientException ex) {
            log.warn("AI adapter failed to load model list", ex);
            return buildFallbackModels();
        }
    }

    public List<KnowledgeBaseOption> getKnowledgeBases() {
        if (!properties.isEnabled()) {
            return new ArrayList<KnowledgeBaseOption>();
        }

        try {
            KnowledgeBaseOption[] response = restTemplate.getForObject(
                    properties.buildKnowledgeBasesUrl(),
                    KnowledgeBaseOption[].class
            );
            if (response == null) {
                return new ArrayList<KnowledgeBaseOption>();
            }
            return Arrays.asList(response);
        } catch (RestClientException ex) {
            log.warn("AI adapter failed to load knowledge base list", ex);
            return new ArrayList<KnowledgeBaseOption>();
        }
    }

    public List<KnowledgeBaseOption> getMerchantKnowledgeBases() {
        if (!properties.isEnabled()) {
            return new ArrayList<KnowledgeBaseOption>();
        }

        try {
            KnowledgeBaseOption[] response = restTemplate.getForObject(
                    properties.buildMerchantKnowledgeBasesUrl(),
                    KnowledgeBaseOption[].class
            );
            if (response == null) {
                return new ArrayList<KnowledgeBaseOption>();
            }
            return Arrays.asList(response);
        } catch (RestClientException ex) {
            log.warn("AI adapter failed to load merchant knowledge base list", ex);
            return new ArrayList<KnowledgeBaseOption>();
        }
    }

    public KnowledgeBaseCreateResponse createKnowledgeBase(KnowledgeBaseCreateRequest request) {
        return restTemplate.postForObject(
                properties.buildMerchantKnowledgeBasesUrl(),
                request,
                KnowledgeBaseCreateResponse.class
        );
    }

    public KnowledgeBaseDocument importTextDocument(String knowledgeBaseId, KnowledgeBaseDocumentTextRequest request) {
        return restTemplate.postForObject(
                properties.buildMerchantKnowledgeBaseTextImportUrl(knowledgeBaseId),
                request,
                KnowledgeBaseDocument.class
        );
    }

    public KnowledgeBaseDocument importPdfDocument(String knowledgeBaseId, String title, String filename, byte[] content) {
        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        body.add("title", title == null ? "" : title);
        body.add("file", new NamedByteArrayResource(content, filename));

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.MULTIPART_FORM_DATA);

        return restTemplate.postForObject(
                properties.buildMerchantKnowledgeBasePdfImportUrl(knowledgeBaseId),
                new HttpEntity<>(body, headers),
                KnowledgeBaseDocument.class
        );
    }

    public KnowledgeBaseUploadTxtResponse uploadTxtKnowledgeBase(String name, String description, String filename, byte[] content) {
        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        body.add("name", name == null ? "" : name);
        body.add("description", description == null ? "" : description);
        body.add("file", new NamedByteArrayResource(content, filename));

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.MULTIPART_FORM_DATA);

        return restTemplate.postForObject(
                properties.buildMerchantKnowledgeBaseUploadTxtUrl(),
                new HttpEntity<>(body, headers),
                KnowledgeBaseUploadTxtResponse.class
        );
    }

    public List<KnowledgeBaseDocument> getKnowledgeBaseDocuments(String knowledgeBaseId) {
        try {
            KnowledgeBaseDocument[] response = restTemplate.getForObject(
                    properties.buildMerchantKnowledgeBaseDocumentsUrl(knowledgeBaseId),
                    KnowledgeBaseDocument[].class
            );
            if (response == null) {
                return new ArrayList<KnowledgeBaseDocument>();
            }
            return Arrays.asList(response);
        } catch (RestClientException ex) {
            log.warn("AI adapter failed to load knowledge base documents for {}", knowledgeBaseId, ex);
            return new ArrayList<KnowledgeBaseDocument>();
        }
    }

    private boolean isTimeoutException(Throwable throwable) {
        Throwable current = throwable;
        while (current != null) {
            if (current instanceof SocketTimeoutException) {
                return true;
            }
            String message = current.getMessage();
            if (message != null && message.toLowerCase().contains("timed out")) {
                return true;
            }
            current = current.getCause();
        }
        return false;
    }

    private List<AiModelOption> buildFallbackModels() {
        List<AiModelOption> models = new ArrayList<>();

        AiModelOption mock = new AiModelOption();
        mock.setId("mock:mock-product-copy-v1");
        mock.setLabel("Mock / mock-product-copy-v1");
        mock.setProvider("mock");
        mock.setModelName("mock-product-copy-v1");
        mock.setDescription("Java 侧内置 fallback 模型列表");
        models.add(mock);

        return models;
    }

    private static class NamedByteArrayResource extends ByteArrayResource {
        private final String filename;

        private NamedByteArrayResource(byte[] byteArray, String filename) {
            super(byteArray == null ? new byte[0] : byteArray);
            this.filename = filename == null || filename.trim().isEmpty() ? "knowledge.txt" : filename.trim();
        }

        @Override
        public String getFilename() {
            return filename;
        }
    }
}





