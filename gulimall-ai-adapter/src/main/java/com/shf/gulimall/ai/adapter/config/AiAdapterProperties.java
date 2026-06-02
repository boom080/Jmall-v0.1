package com.shf.gulimall.ai.adapter.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

import java.util.Arrays;
import java.util.List;

@ConfigurationProperties(prefix = "jrunmall.ai")
public class AiAdapterProperties {

    private boolean enabled = true;
    private String baseUrl = "http://127.0.0.1:18080";
    private String productCopyPath = "/api/product-copy/generate";
    private String modelsPath = "/api/models";
    private String knowledgeBasesPath = "/api/knowledge-bases";
    private String merchantKnowledgeBasesPath = "/api/merchant/knowledge-bases";
    private int connectTimeoutMs = 2000;
    private int readTimeoutMs = 5000;
    private boolean langchain4jEnabled = true;
    private String langchain4jApiKey = "";
    private String langchain4jBaseUrl = "https://api.openai.com/v1";
    private String langchain4jModels = "gpt-4o-mini";
    private double langchain4jTemperature = 0.4D;
    private String deepseekApiKey = "";
    private String deepseekBaseUrl = "https://api.deepseek.com";
    private String deepseekModel = "deepseek-chat";
    private String deepseekModels = "";
    private String qwenApiKey = "";
    private String qwenBaseUrl = "https://dashscope.aliyuncs.com/compatible-mode/v1";
    private String qwenModel = "qwen3-max";
    private String qwenModels = "";

    public boolean isEnabled() {
        return enabled;
    }

    public void setEnabled(boolean enabled) {
        this.enabled = enabled;
    }

    public String getBaseUrl() {
        return baseUrl;
    }

    public void setBaseUrl(String baseUrl) {
        this.baseUrl = baseUrl;
    }

    public String getProductCopyPath() {
        return productCopyPath;
    }

    public void setProductCopyPath(String productCopyPath) {
        this.productCopyPath = productCopyPath;
    }

    public String getModelsPath() {
        return modelsPath;
    }

    public void setModelsPath(String modelsPath) {
        this.modelsPath = modelsPath;
    }

    public String getKnowledgeBasesPath() {
        return knowledgeBasesPath;
    }

    public void setKnowledgeBasesPath(String knowledgeBasesPath) {
        this.knowledgeBasesPath = knowledgeBasesPath;
    }

    public int getConnectTimeoutMs() {
        return connectTimeoutMs;
    }

    public void setConnectTimeoutMs(int connectTimeoutMs) {
        this.connectTimeoutMs = connectTimeoutMs;
    }

    public int getReadTimeoutMs() {
        return readTimeoutMs;
    }

    public void setReadTimeoutMs(int readTimeoutMs) {
        this.readTimeoutMs = readTimeoutMs;
    }

    public String buildProductCopyUrl() {
        return buildUrl(productCopyPath);
    }

    public boolean isLangchain4jEnabled() {
        return langchain4jEnabled;
    }

    public void setLangchain4jEnabled(boolean langchain4jEnabled) {
        this.langchain4jEnabled = langchain4jEnabled;
    }

    public String getLangchain4jApiKey() {
        return langchain4jApiKey;
    }

    public void setLangchain4jApiKey(String langchain4jApiKey) {
        this.langchain4jApiKey = langchain4jApiKey;
    }

    public String getLangchain4jBaseUrl() {
        return langchain4jBaseUrl;
    }

    public void setLangchain4jBaseUrl(String langchain4jBaseUrl) {
        this.langchain4jBaseUrl = langchain4jBaseUrl;
    }

    public String getLangchain4jModels() {
        return langchain4jModels;
    }

    public void setLangchain4jModels(String langchain4jModels) {
        this.langchain4jModels = langchain4jModels;
    }

    public double getLangchain4jTemperature() {
        return langchain4jTemperature;
    }

    public void setLangchain4jTemperature(double langchain4jTemperature) {
        this.langchain4jTemperature = langchain4jTemperature;
    }

    public List<String> resolveLangchain4jModels() {
        if (langchain4jModels == null || langchain4jModels.trim().isEmpty()) {
            return Arrays.asList("gpt-4o-mini");
        }
        return Arrays.asList(langchain4jModels.split("\\s*,\\s*"));
    }

    public String getDeepseekApiKey() {
        return deepseekApiKey;
    }

    public void setDeepseekApiKey(String deepseekApiKey) {
        this.deepseekApiKey = deepseekApiKey;
    }

    public String getDeepseekBaseUrl() {
        return deepseekBaseUrl;
    }

    public void setDeepseekBaseUrl(String deepseekBaseUrl) {
        this.deepseekBaseUrl = deepseekBaseUrl;
    }

    public String getDeepseekModel() {
        return deepseekModel;
    }

    public void setDeepseekModel(String deepseekModel) {
        this.deepseekModel = deepseekModel;
    }

    public String getDeepseekModels() {
        return deepseekModels;
    }

    public void setDeepseekModels(String deepseekModels) {
        this.deepseekModels = deepseekModels;
    }

    public List<String> resolveDeepseekModels() {
        return resolveProviderModels(deepseekModels, deepseekModel, "deepseek-chat");
    }

    public String getQwenApiKey() {
        return qwenApiKey;
    }

    public void setQwenApiKey(String qwenApiKey) {
        this.qwenApiKey = qwenApiKey;
    }

    public String getQwenBaseUrl() {
        return qwenBaseUrl;
    }

    public void setQwenBaseUrl(String qwenBaseUrl) {
        this.qwenBaseUrl = qwenBaseUrl;
    }

    public String getQwenModel() {
        return qwenModel;
    }

    public void setQwenModel(String qwenModel) {
        this.qwenModel = qwenModel;
    }

    public String getQwenModels() {
        return qwenModels;
    }

    public void setQwenModels(String qwenModels) {
        this.qwenModels = qwenModels;
    }

    public List<String> resolveQwenModels() {
        return resolveProviderModels(qwenModels, qwenModel, "qwen3-max");
    }

    public String buildModelsUrl() {
        return buildUrl(modelsPath);
    }

    public String buildKnowledgeBasesUrl() {
        return buildUrl(knowledgeBasesPath);
    }

    public String getMerchantKnowledgeBasesPath() {
        return merchantKnowledgeBasesPath;
    }

    public void setMerchantKnowledgeBasesPath(String merchantKnowledgeBasesPath) {
        this.merchantKnowledgeBasesPath = merchantKnowledgeBasesPath;
    }

    public String buildMerchantKnowledgeBasesUrl() {
        return buildUrl(merchantKnowledgeBasesPath);
    }

    public String buildMerchantKnowledgeBaseDocumentsUrl(String knowledgeBaseId) {
        return buildUrl(merchantKnowledgeBasesPath + "/" + knowledgeBaseId + "/documents");
    }

    public String buildMerchantKnowledgeBaseTextImportUrl(String knowledgeBaseId) {
        return buildUrl(merchantKnowledgeBasesPath + "/" + knowledgeBaseId + "/documents/text");
    }

    public String buildMerchantKnowledgeBasePdfImportUrl(String knowledgeBaseId) {
        return buildUrl(merchantKnowledgeBasesPath + "/" + knowledgeBaseId + "/documents/pdf");
    }

    public String buildMerchantKnowledgeBaseUploadTxtUrl() {
        return buildUrl(merchantKnowledgeBasesPath + "/upload-txt");
    }

    private String buildUrl(String path) {
        String normalizedBaseUrl = trimTrailingSlash(baseUrl);
        String normalizedPath = path.startsWith("/") ? path : "/" + path;
        return normalizedBaseUrl + normalizedPath;
    }

    private String trimTrailingSlash(String value) {
        if (value == null || value.isEmpty()) {
            return "";
        }
        if (value.endsWith("/")) {
            return value.substring(0, value.length() - 1);
        }
        return value;
    }

    private List<String> resolveProviderModels(String models, String model, String defaultModel) {
        String configuredModels = models == null ? "" : models.trim();
        if (!configuredModels.isEmpty()) {
            return Arrays.asList(configuredModels.split("\\s*,\\s*"));
        }
        String configuredModel = model == null ? "" : model.trim();
        if (!configuredModel.isEmpty()) {
            return Arrays.asList(configuredModel);
        }
        return Arrays.asList(defaultModel);
    }
}





