package com.shf.gulimall.ai.adapter.model;

import java.util.ArrayList;
import java.util.List;

public class ProductCopyAiRequest {

    private String title;
    private String category;
    private List<String> sellingPoints = new ArrayList<>();
    private String tone;
    private String modelProvider;
    private String modelName;
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





