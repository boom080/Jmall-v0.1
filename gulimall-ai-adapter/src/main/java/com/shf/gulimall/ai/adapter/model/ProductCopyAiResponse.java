package com.shf.gulimall.ai.adapter.model;

import java.util.ArrayList;
import java.util.List;

public class ProductCopyAiResponse {

    private String generatedTitle;
    private List<String> highlights = new ArrayList<>();
    private String summary;
    private List<String> pendingMerchantConfirmations = new ArrayList<>();
    private String provider;
    private boolean mock;
    private boolean success = true;
    private String message = "商品文案生成成功";
    private String response_source = "no_rag_fallback";
    private List<RagUsedChunk> usedChunks = new ArrayList<>();
    private List<RagUsedChunk> citations = new ArrayList<>();
    private String embeddingProvider = "";

    public static ProductCopyAiResponse disabledFallback(ProductCopyAiRequest request) {
        return failedFallback(request, "java-disabled-fallback",
                "Jrunmall.ai.enabled=false，当前返回 Java 本地降级结果。");
    }

    public static ProductCopyAiResponse failedFallback(ProductCopyAiRequest request, String provider, String message) {
        ProductCopyAiResponse response = new ProductCopyAiResponse();
        response.setGeneratedTitle("AI 降级文案 | " + safeTitle(request));
        response.setHighlights(buildFallbackHighlights(request));
        response.setSummary(message);
        response.setProvider(provider);
        response.setMock(true);
        response.setSuccess(false);
        response.setMessage(message);
        return response;
    }

    public ProductCopyAiResponse normalizeSuccess(ProductCopyAiRequest request) {
        if (!hasText(generatedTitle)) {
            String title = safeTitle(request);
            String category = request == null ? "" : safeText(request.getCategory());
            this.generatedTitle = hasText(category) ? "智能推荐 | " + title + " | " + category : "智能推荐 | " + title;
        }
        if (highlights == null || highlights.isEmpty()) {
            this.highlights = buildFallbackHighlights(request);
        }
        if (!hasText(summary)) {
            this.summary = "商品文案生成成功，当前结果可继续替换为真实 AI Provider。";
        }
        if (pendingMerchantConfirmations == null) {
            this.pendingMerchantConfirmations = new ArrayList<>();
        }
        if (!hasText(provider)) {
            this.provider = "python-mock-ai";
        }
        if (!hasText(message)) {
            this.message = "商品文案生成成功";
        }
        this.success = true;
        return this;
    }

    private static List<String> buildFallbackHighlights(ProductCopyAiRequest request) {
        List<String> requestHighlights = request == null ? null : request.getSellingPoints();
        List<String> highlights = new ArrayList<>();
        if (requestHighlights != null) {
            for (String point : requestHighlights) {
                if (hasText(point)) {
                    highlights.add(point.trim());
                }
            }
        }
        if (highlights.isEmpty()) {
            highlights.add("结构保持稳定");
            highlights.add("支持本地联调");
            highlights.add("可平滑替换真实模型");
        }
        return highlights;
    }

    private static String safeTitle(ProductCopyAiRequest request) {
        if (request == null || !hasText(request.getTitle())) {
            return "未命名商品";
        }
        return request.getTitle().trim();
    }

    private static String safeText(String value) {
        return value == null ? "" : value.trim();
    }

    private static boolean hasText(String value) {
        return value != null && !value.trim().isEmpty();
    }

    public String getGeneratedTitle() {
        return generatedTitle;
    }

    public void setGeneratedTitle(String generatedTitle) {
        this.generatedTitle = generatedTitle;
    }

    public List<String> getHighlights() {
        return highlights;
    }

    public void setHighlights(List<String> highlights) {
        this.highlights = highlights;
    }

    public String getSummary() {
        return summary;
    }

    public void setSummary(String summary) {
        this.summary = summary;
    }

    public List<String> getPendingMerchantConfirmations() {
        return pendingMerchantConfirmations;
    }

    public void setPendingMerchantConfirmations(List<String> pendingMerchantConfirmations) {
        this.pendingMerchantConfirmations = pendingMerchantConfirmations;
    }

    public String getProvider() {
        return provider;
    }

    public void setProvider(String provider) {
        this.provider = provider;
    }

    public boolean isMock() {
        return mock;
    }

    public void setMock(boolean mock) {
        this.mock = mock;
    }

    public boolean isSuccess() {
        return success;
    }

    public void setSuccess(boolean success) {
        this.success = success;
    }

    public String getMessage() {
        return message;
    }

    public void setMessage(String message) {
        this.message = message;
    }

    public String getResponse_source() {
        return response_source;
    }

    public void setResponse_source(String response_source) {
        this.response_source = response_source;
    }

    public List<RagUsedChunk> getUsedChunks() {
        return usedChunks;
    }

    public void setUsedChunks(List<RagUsedChunk> usedChunks) {
        this.usedChunks = usedChunks;
    }

    public List<RagUsedChunk> getCitations() {
        return citations;
    }

    public void setCitations(List<RagUsedChunk> citations) {
        this.citations = citations;
    }

    public String getEmbeddingProvider() {
        return embeddingProvider;
    }

    public void setEmbeddingProvider(String embeddingProvider) {
        this.embeddingProvider = embeddingProvider;
    }
}





