package com.shf.gulimall.product.app.dto;

import javax.validation.constraints.NotBlank;
import javax.validation.constraints.Pattern;
import javax.validation.constraints.Size;
import java.util.ArrayList;
import java.util.List;

public class ProductCopyGenerateRequest {

    private static final String TONE_PATTERN = "(?i)professional|marketing|warm|concise";

    @NotBlank(message = "title 不能为空")
    @Size(max = 120, message = "title 不能超过 120 个字符")
    private String title;

    @Size(max = 60, message = "category 不能超过 60 个字符")
    private String category = "未分类";

    @Size(max = 6, message = "sellingPoints 最多允许 6 条")
    private List<String> sellingPoints = new ArrayList<>();

    @Pattern(regexp = TONE_PATTERN, message = "tone 仅支持 professional、marketing、warm、concise")
    private String tone = "professional";

    @Size(max = 32, message = "modelProvider 不能超过 32 个字符")
    private String modelProvider = "mock";

    @Size(max = 120, message = "modelName 不能超过 120 个字符")
    private String modelName = "mock-product-copy-v1";

    @Size(max = 64, message = "knowledgeBaseId 不能超过 64 个字符")
    private String knowledgeBaseId;

    public String getTitle() {
        return title;
    }

    public void setTitle(String title) {
        this.title = title;
    }

    public String getCategory() {
        return category;
    }

    public void setCategory(String category) {
        this.category = category;
    }

    public List<String> getSellingPoints() {
        return sellingPoints;
    }

    public void setSellingPoints(List<String> sellingPoints) {
        this.sellingPoints = sellingPoints;
    }

    public String getTone() {
        return tone;
    }

    public void setTone(String tone) {
        this.tone = tone;
    }

    public String getModelProvider() {
        return modelProvider;
    }

    public void setModelProvider(String modelProvider) {
        this.modelProvider = modelProvider;
    }

    public String getModelName() {
        return modelName;
    }

    public void setModelName(String modelName) {
        this.modelName = modelName;
    }

    public String getKnowledgeBaseId() {
        return knowledgeBaseId;
    }

    public void setKnowledgeBaseId(String knowledgeBaseId) {
        this.knowledgeBaseId = knowledgeBaseId;
    }
}





