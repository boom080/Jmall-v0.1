package com.shf.gulimall.product.app.service;

import com.shf.gulimall.ai.adapter.model.AiModelOption;
import com.shf.gulimall.ai.adapter.model.KnowledgeBaseCreateRequest;
import com.shf.gulimall.ai.adapter.model.KnowledgeBaseCreateResponse;
import com.shf.gulimall.ai.adapter.model.KnowledgeBaseDocument;
import com.shf.gulimall.ai.adapter.model.KnowledgeBaseDocumentTextRequest;
import com.shf.gulimall.ai.adapter.model.KnowledgeBaseOption;
import com.shf.gulimall.ai.adapter.model.KnowledgeBaseUploadTxtResponse;
import com.shf.gulimall.ai.adapter.model.ProductCopyAiRequest;
import com.shf.gulimall.ai.adapter.model.ProductCopyAiResponse;
import com.shf.gulimall.ai.adapter.model.RagUsedChunk;
import com.shf.gulimall.ai.adapter.service.ProductCopyAiService;
import com.shf.gulimall.product.app.dto.ProductAiKnowledgeBaseOptionResponse;
import com.shf.gulimall.product.app.dto.ProductAiModelOptionResponse;
import com.shf.gulimall.product.app.dto.ProductCopyGenerateRequest;
import com.shf.gulimall.product.app.dto.ProductCopyGenerateResponse;
import com.shf.gulimall.product.app.dto.MerchantKnowledgeBaseCreateResponse;
import com.shf.gulimall.product.app.dto.MerchantKnowledgeBaseDocumentResponse;
import com.shf.gulimall.product.app.dto.MerchantKnowledgeBaseUploadTxtResponse;
import com.shf.gulimall.product.app.dto.RagUsedChunkResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

@Service
public class ProductAiApplicationService {

    private static final Logger log = LoggerFactory.getLogger(ProductAiApplicationService.class);

    private final ProductCopyAiService productCopyAiService;

    public ProductAiApplicationService(ProductCopyAiService productCopyAiService) {
        this.productCopyAiService = productCopyAiService;
    }

    public ProductCopyGenerateResponse generateProductCopy(ProductCopyGenerateRequest request) {
        ProductCopyAiRequest aiRequest = toAiRequest(request);
        try {
            ProductCopyAiResponse aiResponse = productCopyAiService.generateProductCopy(aiRequest);
            if (aiResponse == null) {
                return buildSafeFallbackResponse(aiRequest, "AI 适配层返回空结果，已返回应用层安全降级文案。");
            }
            return toGenerateResponse(aiResponse);
        } catch (Throwable ex) {
            log.warn("Product AI application service fallback triggered", ex);
            return buildSafeFallbackResponse(aiRequest, "AI 调用链路异常，已返回应用层安全降级文案。");
        }
    }

    public List<ProductAiModelOptionResponse> listAvailableModels() {
        List<AiModelOption> models = productCopyAiService.getAvailableModels();
        List<ProductAiModelOptionResponse> responses = new ArrayList<>();
        for (AiModelOption model : models) {
            ProductAiModelOptionResponse response = new ProductAiModelOptionResponse();
            response.setId(model.getId());
            response.setLabel(model.getLabel());
            response.setProvider(model.getProvider());
            response.setModelName(model.getModelName());
            response.setDescription(model.getDescription());
            responses.add(response);
        }
        return responses;
    }

    public List<ProductAiKnowledgeBaseOptionResponse> listKnowledgeBases() {
        List<KnowledgeBaseOption> options = productCopyAiService.getKnowledgeBases();
        List<ProductAiKnowledgeBaseOptionResponse> responses = new ArrayList<>();
        for (KnowledgeBaseOption option : options) {
            ProductAiKnowledgeBaseOptionResponse response = new ProductAiKnowledgeBaseOptionResponse();
            response.setId(option.getId());
            response.setLabel(option.getLabel());
            response.setDescription(option.getDescription());
            response.setDocumentCount(option.getDocumentCount());
            response.setChunkCount(option.getChunkCount());
            response.setEmbeddingStatus(option.getEmbeddingStatus());
            response.setUpdatedAt(option.getUpdatedAt());
            response.setSource(option.getSource());
            responses.add(response);
        }
        return responses;
    }

    public List<ProductAiKnowledgeBaseOptionResponse> listMerchantKnowledgeBases() {
        List<KnowledgeBaseOption> options = productCopyAiService.getMerchantKnowledgeBases();
        List<ProductAiKnowledgeBaseOptionResponse> responses = new ArrayList<>();
        for (KnowledgeBaseOption option : options) {
            ProductAiKnowledgeBaseOptionResponse response = new ProductAiKnowledgeBaseOptionResponse();
            response.setId(option.getId());
            response.setLabel(option.getLabel());
            response.setDescription(option.getDescription());
            response.setDocumentCount(option.getDocumentCount());
            response.setChunkCount(option.getChunkCount());
            response.setEmbeddingStatus(option.getEmbeddingStatus());
            response.setUpdatedAt(option.getUpdatedAt());
            response.setSource(option.getSource());
            responses.add(response);
        }
        return responses;
    }

    public MerchantKnowledgeBaseCreateResponse createMerchantKnowledgeBase(String name, String description) {
        KnowledgeBaseCreateRequest request = new KnowledgeBaseCreateRequest();
        request.setName(normalizeText(name, "未命名知识库"));
        request.setDescription(normalizeNullableText(description));

        KnowledgeBaseCreateResponse response = productCopyAiService.createKnowledgeBase(request);
        if (response == null) {
            throw new IllegalStateException("AI 知识库创建接口返回空结果");
        }
        MerchantKnowledgeBaseCreateResponse result = new MerchantKnowledgeBaseCreateResponse();
        result.setId(response.getId());
        result.setLabel(response.getLabel());
        result.setDescription(response.getDescription());
        result.setEmbeddingStatus(response.getEmbeddingStatus());
        result.setSource(response.getSource());
        result.setUpdatedAt(response.getUpdatedAt());
        return result;
    }

    public MerchantKnowledgeBaseDocumentResponse importMerchantKnowledgeBaseTextDocument(
            String knowledgeBaseId,
            String title,
            String content
    ) {
        KnowledgeBaseDocumentTextRequest request = new KnowledgeBaseDocumentTextRequest();
        request.setTitle(normalizeText(title, "未命名文本"));
        request.setContent(normalizeText(content, ""));
        KnowledgeBaseDocument document = productCopyAiService.importTextDocument(knowledgeBaseId, request);
        return toDocumentResponse(document);
    }

    public MerchantKnowledgeBaseDocumentResponse importMerchantKnowledgeBasePdfDocument(
            String knowledgeBaseId,
            String title,
            String filename,
            byte[] content
    ) {
        if (content == null || content.length == 0) {
            throw new IllegalArgumentException("PDF 文件不能为空");
        }
        KnowledgeBaseDocument document = productCopyAiService.importPdfDocument(
                knowledgeBaseId,
                normalizeNullableText(title),
                normalizeText(filename, "knowledge.pdf"),
                content
        );
        return toDocumentResponse(document);
    }

    public MerchantKnowledgeBaseUploadTxtResponse uploadTxtKnowledgeBase(
            String name,
            String description,
            String filename,
            byte[] content
    ) {
        if (content == null || content.length == 0) {
            throw new IllegalArgumentException("txt 文件不能为空");
        }
        KnowledgeBaseUploadTxtResponse response = productCopyAiService.uploadTxtKnowledgeBase(
                normalizeText(name, "未命名知识库"),
                normalizeNullableText(description),
                normalizeText(filename, "knowledge.txt"),
                content
        );
        if (response == null) {
            throw new IllegalStateException("AI txt 上传接口返回空结果");
        }
        MerchantKnowledgeBaseUploadTxtResponse result = new MerchantKnowledgeBaseUploadTxtResponse();
        result.setKnowledgeBaseId(response.getKnowledgeBaseId());
        result.setName(response.getName());
        result.setDocumentId(response.getDocumentId());
        result.setChunkCount(response.getChunkCount());
        result.setEmbeddingProvider(response.getEmbeddingProvider());
        result.setStatus(response.getStatus());
        return result;
    }

    public List<MerchantKnowledgeBaseDocumentResponse> listMerchantKnowledgeBaseDocuments(String knowledgeBaseId) {
        List<KnowledgeBaseDocument> documents = productCopyAiService.getKnowledgeBaseDocuments(knowledgeBaseId);
        List<MerchantKnowledgeBaseDocumentResponse> responses = new ArrayList<>();
        for (KnowledgeBaseDocument document : documents) {
            responses.add(toDocumentResponse(document));
        }
        return responses;
    }

    private ProductCopyAiRequest toAiRequest(ProductCopyGenerateRequest request) {
        ProductCopyAiRequest aiRequest = new ProductCopyAiRequest();
        aiRequest.setTitle(normalizeText(request.getTitle(), "未命名商品"));
        aiRequest.setCategory(normalizeText(request.getCategory(), "未分类"));
        aiRequest.setTone(normalizeText(request.getTone(), "professional").toLowerCase(Locale.ROOT));
        aiRequest.setSellingPoints(normalizeSellingPoints(request.getSellingPoints()));
        aiRequest.setModelProvider(normalizeText(request.getModelProvider(), "mock").toLowerCase(Locale.ROOT));
        aiRequest.setModelName(normalizeText(request.getModelName(), "mock-product-copy-v1"));
        aiRequest.setKnowledgeBaseId(normalizeNullableText(request.getKnowledgeBaseId()));
        return aiRequest;
    }

    private ProductCopyGenerateResponse toGenerateResponse(ProductCopyAiResponse aiResponse) {
        ProductCopyGenerateResponse response = new ProductCopyGenerateResponse();
        response.setGeneratedTitle(aiResponse.getGeneratedTitle());
        response.setHighlights(aiResponse.getHighlights() == null ? new ArrayList<String>() : new ArrayList<>(aiResponse.getHighlights()));
        response.setSummary(aiResponse.getSummary());
        response.setProvider(aiResponse.getProvider());
        response.setMock(aiResponse.isMock());
        response.setSuccess(aiResponse.isSuccess());
        response.setMessage(aiResponse.getMessage());
        response.setResponse_source(aiResponse.getResponse_source());
        response.setUsedChunks(toUsedChunkResponses(aiResponse.getUsedChunks()));
        response.setCitations(toUsedChunkResponses(aiResponse.getCitations()));
        response.setEmbeddingProvider(aiResponse.getEmbeddingProvider());
        return response;
    }

    private List<String> normalizeSellingPoints(List<String> sellingPoints) {
        List<String> normalized = new ArrayList<>();
        if (sellingPoints == null) {
            return normalized;
        }
        for (String point : sellingPoints) {
            if (point == null) {
                continue;
            }
            String trimmed = point.trim();
            if (!trimmed.isEmpty()) {
                normalized.add(trimmed);
            }
        }
        return normalized;
    }

    private String normalizeText(String value, String defaultValue) {
        if (value == null) {
            return defaultValue;
        }
        String trimmed = value.trim();
        return trimmed.isEmpty() ? defaultValue : trimmed;
    }

    private String normalizeNullableText(String value) {
        if (value == null) {
            return null;
        }
        String trimmed = value.trim();
        return trimmed.isEmpty() ? null : trimmed;
    }

    private ProductCopyGenerateResponse buildSafeFallbackResponse(ProductCopyAiRequest aiRequest, String message) {
        ProductCopyGenerateResponse response = new ProductCopyGenerateResponse();
        response.setGeneratedTitle("AI 应用层降级文案 | " + aiRequest.getTitle());
        response.setHighlights(aiRequest.getSellingPoints().isEmpty() ? buildDefaultHighlights() : new ArrayList<>(aiRequest.getSellingPoints()));
        response.setSummary(message);
        response.setProvider("product-ai-application-fallback");
        response.setMock(true);
        response.setSuccess(false);
        response.setMessage(message);
        response.setResponse_source("no_rag_fallback");
        response.setEmbeddingProvider("");
        return response;
    }

    private List<String> buildDefaultHighlights() {
        List<String> highlights = new ArrayList<>();
        highlights.add("结构保持稳定");
        highlights.add("适合后台联调");
        highlights.add("可平滑替换真实模型");
        return highlights;
    }

    private MerchantKnowledgeBaseDocumentResponse toDocumentResponse(KnowledgeBaseDocument document) {
        if (document == null) {
            throw new IllegalStateException("AI 知识库文档接口返回空结果");
        }
        MerchantKnowledgeBaseDocumentResponse response = new MerchantKnowledgeBaseDocumentResponse();
        response.setId(document.getId());
        response.setKnowledgeBaseId(document.getKnowledgeBaseId());
        response.setTitle(document.getTitle());
        response.setChunkCount(document.getChunkCount());
        response.setEmbeddingStatus(document.getEmbeddingStatus());
        response.setUpdatedAt(document.getUpdatedAt());
        response.setContentPreview(document.getContentPreview());
        return response;
    }

    private List<RagUsedChunkResponse> toUsedChunkResponses(List<RagUsedChunk> chunks) {
        List<RagUsedChunkResponse> responses = new ArrayList<>();
        if (chunks == null) {
            return responses;
        }
        for (RagUsedChunk chunk : chunks) {
            if (chunk == null) {
                continue;
            }
            RagUsedChunkResponse response = new RagUsedChunkResponse();
            response.setChunkId(chunk.getChunkId());
            response.setDocumentId(chunk.getDocumentId());
            response.setKnowledgeBaseId(chunk.getKnowledgeBaseId());
            response.setContent(chunk.getContent());
            response.setScore(chunk.getScore());
            response.setSourceFilename(chunk.getSourceFilename());
            response.setChunkIndex(chunk.getChunkIndex());
            response.setMetadata(chunk.getMetadata());
            responses.add(response);
        }
        return responses;
    }
}





