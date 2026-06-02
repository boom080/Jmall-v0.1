package com.shf.gulimall.product.app.dto;

import java.util.ArrayList;
import java.util.List;

public class ProductCopyGenerateResponse {

    private String generatedTitle;
    private List<String> highlights = new ArrayList<>();
    private String summary;
    private String provider;
    private boolean mock;
    private boolean success;
    private String message;
    private String response_source;
    private List<RagUsedChunkResponse> usedChunks = new ArrayList<>();
    private List<RagUsedChunkResponse> citations = new ArrayList<>();
    private String embeddingProvider;

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

    public List<RagUsedChunkResponse> getUsedChunks() {
        return usedChunks;
    }

    public void setUsedChunks(List<RagUsedChunkResponse> usedChunks) {
        this.usedChunks = usedChunks;
    }

    public List<RagUsedChunkResponse> getCitations() {
        return citations;
    }

    public void setCitations(List<RagUsedChunkResponse> citations) {
        this.citations = citations;
    }

    public String getEmbeddingProvider() {
        return embeddingProvider;
    }

    public void setEmbeddingProvider(String embeddingProvider) {
        this.embeddingProvider = embeddingProvider;
    }
}





