package com.shf.gulimall.ai.adapter.client;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.shf.gulimall.ai.adapter.config.AiAdapterProperties;
import com.shf.gulimall.ai.adapter.model.AiModelOption;
import com.shf.gulimall.ai.adapter.model.KnowledgeBaseDocument;
import com.shf.gulimall.ai.adapter.model.ProductCopyAiRequest;
import com.shf.gulimall.ai.adapter.model.ProductCopyAiResponse;
import dev.langchain4j.model.chat.ChatLanguageModel;
import dev.langchain4j.model.openai.OpenAiChatModel;

import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

public class LangChain4jProductCopyClient {

    private static final String PROVIDER = "langchain4j-openai";
    private static final String DEEPSEEK_PROVIDER = "deepseek";
    private static final String QWEN_PROVIDER = "qwen";
    private static final String GENERIC_API_KEY_HINT = "请在 .env.local 或启动环境变量中填写 JRUNMALL_AI_LANGCHAIN4J_API_KEY。";
    private static final String DEEPSEEK_API_KEY_HINT = "请在 .env.local 或启动环境变量中填写 JRUNMALL_AI_DEEPSEEK_API_KEY。";
    private static final String QWEN_API_KEY_HINT = "请在 .env.local 或启动环境变量中填写 JRUNMALL_AI_QWEN_API_KEY。";
    private static final String[] GENERIC_API_KEY_NAMES = {"JRUNMALL_AI_LANGCHAIN4J_API_KEY", "GULIMALL_AI_LANGCHAIN4J_API_KEY", "LANGCHAIN4J_API_KEY", "OPENAI_API_KEY"};
    private static final String[] DEEPSEEK_API_KEY_NAMES = {"JRUNMALL_AI_DEEPSEEK_API_KEY", "GULIMALL_AI_DEEPSEEK_API_KEY", "DEEPSEEK_API_KEY"};
    private static final String[] QWEN_API_KEY_NAMES = {"JRUNMALL_AI_QWEN_API_KEY", "GULIMALL_AI_QWEN_API_KEY", "QWEN_API_KEY", "DASHSCOPE_API_KEY", "ALIYUN_API_KEY", "ALIBABA_CLOUD_API_KEY"};

    private final AiAdapterProperties properties;
    private final ObjectMapper objectMapper = new ObjectMapper();

    public LangChain4jProductCopyClient(AiAdapterProperties properties) {
        this.properties = properties;
    }

    public boolean supports(ProductCopyAiRequest request) {
        if (request == null) {
            return false;
        }
        String provider = safeText(request.getModelProvider()).toLowerCase(Locale.ROOT);
        return PROVIDER.equals(provider) || DEEPSEEK_PROVIDER.equals(provider) || QWEN_PROVIDER.equals(provider);
    }

    public List<AiModelOption> getModelOptions() {
        List<AiModelOption> options = new ArrayList<>();
        if (!properties.isLangchain4jEnabled()) {
            return options;
        }

        if (hasText(resolveDeepseekApiKey())) {
            for (String modelName : properties.resolveDeepseekModels()) {
                addModelOption(options, "DeepSeek", modelName, "DeepSeek OpenAI-compatible endpoint；密钥使用 JRUNMALL_AI_DEEPSEEK_API_KEY。");
            }
        }
        if (hasText(resolveQwenApiKey())) {
            for (String modelName : properties.resolveQwenModels()) {
                addModelOption(options, "Qwen", modelName, "Alibaba Cloud Model Studio OpenAI-compatible endpoint；密钥使用 JRUNMALL_AI_QWEN_API_KEY。");
            }
        }

        if (hasText(resolveGenericApiKey())) {
            for (String modelName : properties.resolveLangchain4jModels()) {
                if (!hasText(modelName)) {
                    continue;
                }
                addModelOption(options, "LangChain4j", modelName, "Java LangChain4j 直连通用 OpenAI-compatible Chat 模型；密钥使用 JRUNMALL_AI_LANGCHAIN4J_API_KEY。");
            }
        }
        return options;
    }

    public ProductCopyAiResponse generate(ProductCopyAiRequest request, List<KnowledgeBaseDocument> documents) {
        if (!properties.isLangchain4jEnabled()) {
            return ProductCopyAiResponse.failedFallback(request, "langchain4j-disabled", "LangChain4j 通道未开启。");
        }
        ModelEndpoint endpoint = resolveEndpoint(request);
        if (!hasText(endpoint.apiKey)) {
            return ProductCopyAiResponse.failedFallback(request, endpoint.missingKeyProvider, endpoint.missingKeyMessage);
        }

        try {
            ChatLanguageModel model = OpenAiChatModel.builder()
                    .apiKey(endpoint.apiKey.trim())
                    .baseUrl(trimTrailingSlash(endpoint.baseUrl))
                    .modelName(endpoint.modelName)
                    .temperature(properties.getLangchain4jTemperature())
                    .timeout(Duration.ofMillis(Math.max(properties.getReadTimeoutMs(), 1000)))
                    .build();

            String raw = model.generate(buildPrompt(request, documents));
            ProductCopyAiResponse response = parseModelResponse(raw, request);
            response.setProvider(PROVIDER + ":" + endpoint.modelName);
            response.setMock(false);
            response.setSuccess(true);
            response.setMessage(buildKnowledgeUsageMessage(documents));
            return response.normalizeSuccess(request);
        } catch (RuntimeException ex) {
            return ProductCopyAiResponse.failedFallback(
                    request,
                    PROVIDER + ":" + endpoint.modelName + "-failed",
                    "LangChain4j 调用 " + endpoint.modelName + " 失败：" + sanitizeFailureMessage(ex)
            );
        }
    }

    private void addModelOption(List<AiModelOption> options, String labelPrefix, String modelName, String description) {
        if (!hasText(modelName) || containsModelOption(options, modelName.trim())) {
            return;
        }
        AiModelOption option = new AiModelOption();
        option.setId(PROVIDER + ":" + modelName.trim());
        option.setProvider(PROVIDER);
        option.setModelName(modelName.trim());
        option.setLabel(labelPrefix + " / " + modelName.trim());
        option.setDescription(description);
        options.add(option);
    }

    private boolean containsModelOption(List<AiModelOption> options, String modelName) {
        for (AiModelOption option : options) {
            if (modelName.equals(option.getModelName())) {
                return true;
            }
        }
        return false;
    }

    private ModelEndpoint resolveEndpoint(ProductCopyAiRequest request) {
        String provider = safeText(request.getModelProvider()).toLowerCase(Locale.ROOT);
        String requestedModelName = safeText(request.getModelName());
        if (DEEPSEEK_PROVIDER.equals(provider)) {
            return deepseekEndpoint(providerModelName(requestedModelName, properties.resolveDeepseekModels()));
        }
        if (QWEN_PROVIDER.equals(provider)) {
            return qwenEndpoint(providerModelName(requestedModelName, properties.resolveQwenModels()));
        }

        String modelName = hasText(requestedModelName) ? requestedModelName : firstConfiguredModel();
        if (containsConfiguredModel(properties.resolveDeepseekModels(), modelName)) {
            return deepseekEndpoint(modelName);
        }
        if (containsConfiguredModel(properties.resolveQwenModels(), modelName)) {
            ModelEndpoint qwenEndpoint = qwenEndpoint(modelName);
            if (hasText(qwenEndpoint.apiKey)) {
                return qwenEndpoint;
            }
            ModelEndpoint availableEndpoint = firstAvailableEndpoint();
            return availableEndpoint == null ? qwenEndpoint : availableEndpoint;
        }
        if (looksLikeDeepseekModel(modelName)) {
            return deepseekEndpoint(modelName);
        }
        if (looksLikeQwenModel(modelName)) {
            return qwenEndpoint(modelName);
        }
        ModelEndpoint genericEndpoint = genericEndpoint(modelName);
        if (hasText(genericEndpoint.apiKey)) {
            return genericEndpoint;
        }
        ModelEndpoint availableEndpoint = firstAvailableEndpoint();
        return availableEndpoint == null ? genericEndpoint : availableEndpoint;
    }

    private String providerModelName(String requestedModelName, List<String> configuredModels) {
        if (hasText(requestedModelName)) {
            return requestedModelName.trim();
        }
        String configuredModel = firstProviderModel(configuredModels);
        return hasText(configuredModel) ? configuredModel : firstConfiguredModel();
    }

    private String firstConfiguredModel() {
        ModelEndpoint availableEndpoint = firstAvailableEndpoint();
        if (availableEndpoint != null) {
            return availableEndpoint.modelName;
        }
        String deepseekModel = firstProviderModel(properties.resolveDeepseekModels());
        if (hasText(deepseekModel)) {
            return deepseekModel;
        }
        String qwenModel = firstProviderModel(properties.resolveQwenModels());
        if (hasText(qwenModel)) {
            return qwenModel;
        }
        return properties.resolveLangchain4jModels().get(0);
    }

    private ModelEndpoint firstAvailableEndpoint() {
        String deepseekModel = firstProviderModel(properties.resolveDeepseekModels());
        if (hasText(deepseekModel) && hasText(resolveDeepseekApiKey())) {
            return deepseekEndpoint(deepseekModel);
        }
        String qwenModel = firstProviderModel(properties.resolveQwenModels());
        if (hasText(qwenModel) && hasText(resolveQwenApiKey())) {
            return qwenEndpoint(qwenModel);
        }
        String genericModel = firstProviderModel(properties.resolveLangchain4jModels());
        if (hasText(genericModel) && hasText(resolveGenericApiKey())) {
            return genericEndpoint(genericModel);
        }
        return null;
    }

    private ModelEndpoint deepseekEndpoint(String modelName) {
        return new ModelEndpoint(
                modelName,
                properties.getDeepseekBaseUrl(),
                resolveDeepseekApiKey(),
                "langchain4j-deepseek-missing-api-key",
                DEEPSEEK_API_KEY_HINT
        );
    }

    private ModelEndpoint qwenEndpoint(String modelName) {
        return new ModelEndpoint(
                modelName,
                properties.getQwenBaseUrl(),
                resolveQwenApiKey(),
                "langchain4j-qwen-missing-api-key",
                QWEN_API_KEY_HINT
        );
    }

    private ModelEndpoint genericEndpoint(String modelName) {
        return new ModelEndpoint(
                modelName,
                properties.getLangchain4jBaseUrl(),
                resolveGenericApiKey(),
                "langchain4j-missing-api-key",
                GENERIC_API_KEY_HINT
        );
    }

    private String resolveDeepseekApiKey() {
        return LocalAiKeyResolver.resolve(properties.getDeepseekApiKey(), DEEPSEEK_API_KEY_NAMES);
    }

    private String resolveQwenApiKey() {
        return LocalAiKeyResolver.resolve(properties.getQwenApiKey(), QWEN_API_KEY_NAMES);
    }

    private String resolveGenericApiKey() {
        return LocalAiKeyResolver.resolve(properties.getLangchain4jApiKey(), GENERIC_API_KEY_NAMES);
    }

    private String firstProviderModel(List<String> models) {
        if (models == null) {
            return "";
        }
        for (String modelName : models) {
            if (hasText(modelName)) {
                return modelName.trim();
            }
        }
        return "";
    }

    private boolean containsConfiguredModel(List<String> models, String modelName) {
        if (!hasText(modelName)) {
            return false;
        }
        for (String model : models) {
            if (modelName.equalsIgnoreCase(safeText(model))) {
                return true;
            }
        }
        return false;
    }

    private boolean looksLikeDeepseekModel(String modelName) {
        return safeText(modelName).toLowerCase(Locale.ROOT).startsWith("deepseek");
    }

    private boolean looksLikeQwenModel(String modelName) {
        String normalized = safeText(modelName).toLowerCase(Locale.ROOT);
        return normalized.startsWith("qwen") || normalized.startsWith("qwq");
    }

    private String buildPrompt(ProductCopyAiRequest request, List<KnowledgeBaseDocument> documents) {
        StringBuilder builder = new StringBuilder();
        builder.append("你是 Jrunmall 商家端商品运营文案助手。请只输出 JSON，不要输出 Markdown。\n");
        builder.append("JSON 字段必须包含 generatedTitle、highlights、summary、pendingMerchantConfirmations。\n");
        builder.append("generatedTitle 是一个商品标题；highlights 是 3 到 5 条中文卖点数组；summary 是 80 到 140 字中文摘要。\n");
        builder.append("pendingMerchantConfirmations 是待商家确认信息数组，记录商品输入未提供证据但生成前需要确认的参数、认证、保修、适用人数、功效或活动信息。\n");
        builder.append("【事实约束】\n");
        builder.append("- 商品输入中没有提供的信息，不要编造。\n");
        builder.append("- 不要主动生成未提供的认证、销量、排名、保修、适用人数、材质等级。\n");
        builder.append("- 如果信息不足，用“请商家确认……”表达。\n");
        builder.append("- 可以根据类目做一般性文案组织，但不能把一般经验写成确定事实。\n");
        builder.append("- RAG 资料只作为文案结构和写法参考，不代表当前商品一定具备其中所有特性。\n");
        builder.append("- 如果出现减少油烟、永不粘锅、3-5人适用、导热均匀、耐用抗腐蚀等高风险表达，且商品输入没有证据，必须改成保守表达或放入待商家确认信息。\n");
        builder.append("商品标题：").append(safeText(request.getTitle())).append("\n");
        builder.append("商品分类：").append(safeText(request.getCategory())).append("\n");
        builder.append("语气风格：").append(safeText(request.getTone())).append("\n");
        builder.append("用户填写卖点：").append(String.join("；", request.getSellingPoints())).append("\n");
        if (documents != null && !documents.isEmpty()) {
            builder.append("知识库检索资料：\n");
            for (KnowledgeBaseDocument document : documents) {
                builder.append("- ").append(safeText(document.getTitle())).append("：")
                        .append(safeText(document.getContentPreview())).append("\n");
            }
        } else {
            builder.append("知识库检索资料：未选择或无可用文档。\n");
        }
        return builder.toString();
    }

    private ProductCopyAiResponse parseModelResponse(String raw, ProductCopyAiRequest request) {
        ProductCopyAiResponse response = new ProductCopyAiResponse();
        try {
            JsonNode root = objectMapper.readTree(extractJson(raw));
            response.setGeneratedTitle(text(root, "generatedTitle"));
            response.setSummary(text(root, "summary"));
            List<String> highlights = new ArrayList<>();
            JsonNode highlightNode = root.get("highlights");
            if (highlightNode != null && highlightNode.isArray()) {
                for (JsonNode item : highlightNode) {
                    if (hasText(item.asText())) {
                        highlights.add(item.asText().trim());
                    }
                }
            }
            response.setHighlights(highlights);
            List<String> pending = new ArrayList<>();
            JsonNode pendingNode = root.get("pendingMerchantConfirmations");
            if (pendingNode != null && pendingNode.isArray()) {
                for (JsonNode item : pendingNode) {
                    if (hasText(item.asText())) {
                        pending.add(item.asText().trim());
                    }
                }
            }
            response.setPendingMerchantConfirmations(pending);
        } catch (Exception ignored) {
            response.setGeneratedTitle("智能推荐 | " + safeText(request.getTitle()));
            response.setHighlights(request.getSellingPoints());
            response.setSummary(hasText(raw) ? raw.trim() : "LangChain4j 已返回结果，但内容为空。");
            response.setPendingMerchantConfirmations(new ArrayList<>());
        }
        return response;
    }

    private String extractJson(String raw) {
        if (raw == null) {
            return "{}";
        }
        int start = raw.indexOf('{');
        int end = raw.lastIndexOf('}');
        if (start >= 0 && end > start) {
            return raw.substring(start, end + 1);
        }
        return raw;
    }

    private String text(JsonNode root, String field) {
        JsonNode node = root.get(field);
        return node == null ? "" : node.asText("");
    }

    private String buildKnowledgeUsageMessage(List<KnowledgeBaseDocument> documents) {
        int documentCount = documents == null ? 0 : documents.size();
        if (documentCount == 0) {
            return "LangChain4j 生成成功；本次未检索到知识库文档。";
        }
        return "LangChain4j 生成成功；已带入 " + documentCount + " 篇知识库文档摘要。";
    }

    private String trimTrailingSlash(String value) {
        if (!hasText(value)) {
            return "https://api.openai.com/v1";
        }
        String result = value.trim();
        while (result.endsWith("/")) {
            result = result.substring(0, result.length() - 1);
        }
        return result;
    }

    private String sanitizeFailureMessage(Throwable throwable) {
        String message = rootMessage(throwable);
        if (!hasText(message)) {
            message = throwable == null ? "unknown error" : throwable.getClass().getSimpleName();
        }
        message = message.replaceAll("(?i)(api[-_ ]?key|authorization|bearer)\\s*[:=]\\s*[^,\\s}]+", "$1=<masked>");
        return message.length() > 240 ? message.substring(0, 240) + "..." : message;
    }

    private String rootMessage(Throwable throwable) {
        Throwable current = throwable;
        Throwable root = throwable;
        while (current != null) {
            root = current;
            current = current.getCause();
        }
        return root == null ? "" : safeText(root.getMessage());
    }

    private static String safeText(String value) {
        return value == null ? "" : value.trim();
    }

    private static boolean hasText(String value) {
        return value != null && !value.trim().isEmpty();
    }

    private static class ModelEndpoint {
        private final String modelName;
        private final String baseUrl;
        private final String apiKey;
        private final String missingKeyProvider;
        private final String missingKeyMessage;

        private ModelEndpoint(String modelName, String baseUrl, String apiKey, String missingKeyProvider, String missingKeyMessage) {
            this.modelName = modelName;
            this.baseUrl = baseUrl;
            this.apiKey = apiKey;
            this.missingKeyProvider = missingKeyProvider;
            this.missingKeyMessage = missingKeyMessage;
        }
    }
}
