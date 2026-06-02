package com.shf.gulimall.ai.adapter.service;

import com.shf.gulimall.ai.adapter.client.AiHttpClient;
import com.shf.gulimall.ai.adapter.client.LangChain4jProductCopyClient;
import com.shf.gulimall.ai.adapter.model.AiModelOption;
import com.shf.gulimall.ai.adapter.model.KnowledgeBaseCreateRequest;
import com.shf.gulimall.ai.adapter.model.KnowledgeBaseCreateResponse;
import com.shf.gulimall.ai.adapter.model.KnowledgeBaseDocument;
import com.shf.gulimall.ai.adapter.model.KnowledgeBaseDocumentTextRequest;
import com.shf.gulimall.ai.adapter.model.KnowledgeBaseOption;
import com.shf.gulimall.ai.adapter.model.KnowledgeBaseUploadTxtResponse;
import com.shf.gulimall.ai.adapter.model.ProductCopyAiRequest;
import com.shf.gulimall.ai.adapter.model.ProductCopyAiResponse;

import java.util.List;

public class ProductCopyAiService {

    private final AiHttpClient aiHttpClient;
    private final LangChain4jProductCopyClient langChain4jProductCopyClient;

    public ProductCopyAiService(AiHttpClient aiHttpClient, LangChain4jProductCopyClient langChain4jProductCopyClient) {
        this.aiHttpClient = aiHttpClient;
        this.langChain4jProductCopyClient = langChain4jProductCopyClient;
    }

    public ProductCopyAiResponse generateProductCopy(ProductCopyAiRequest request) {
        return aiHttpClient.generateProductCopy(request);
    }

    public List<AiModelOption> getAvailableModels() {
        return aiHttpClient.getAvailableModels();
    }

    public List<KnowledgeBaseOption> getKnowledgeBases() {
        return aiHttpClient.getKnowledgeBases();
    }

    public List<KnowledgeBaseOption> getMerchantKnowledgeBases() {
        return aiHttpClient.getMerchantKnowledgeBases();
    }

    public KnowledgeBaseCreateResponse createKnowledgeBase(KnowledgeBaseCreateRequest request) {
        return aiHttpClient.createKnowledgeBase(request);
    }

    public KnowledgeBaseDocument importTextDocument(String knowledgeBaseId, KnowledgeBaseDocumentTextRequest request) {
        return aiHttpClient.importTextDocument(knowledgeBaseId, request);
    }

    public KnowledgeBaseDocument importPdfDocument(String knowledgeBaseId, String title, String filename, byte[] content) {
        return aiHttpClient.importPdfDocument(knowledgeBaseId, title, filename, content);
    }

    public KnowledgeBaseUploadTxtResponse uploadTxtKnowledgeBase(String name, String description, String filename, byte[] content) {
        return aiHttpClient.uploadTxtKnowledgeBase(name, description, filename, content);
    }

    public List<KnowledgeBaseDocument> getKnowledgeBaseDocuments(String knowledgeBaseId) {
        return aiHttpClient.getKnowledgeBaseDocuments(knowledgeBaseId);
    }
}





