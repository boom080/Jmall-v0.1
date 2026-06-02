package com.shf.gulimall.product.app.service;

import com.shf.gulimall.ai.adapter.model.KnowledgeBaseCreateResponse;
import com.shf.gulimall.ai.adapter.model.KnowledgeBaseDocument;
import com.shf.gulimall.ai.adapter.model.KnowledgeBaseOption;
import com.shf.gulimall.ai.adapter.model.KnowledgeBaseUploadTxtResponse;
import com.shf.gulimall.ai.adapter.model.ProductCopyAiRequest;
import com.shf.gulimall.ai.adapter.model.ProductCopyAiResponse;
import com.shf.gulimall.ai.adapter.model.RagUsedChunk;
import com.shf.gulimall.ai.adapter.service.ProductCopyAiService;
import com.shf.gulimall.product.app.dto.MerchantKnowledgeBaseCreateResponse;
import com.shf.gulimall.product.app.dto.MerchantKnowledgeBaseDocumentResponse;
import com.shf.gulimall.product.app.dto.MerchantKnowledgeBaseUploadTxtResponse;
import com.shf.gulimall.product.app.dto.ProductCopyGenerateRequest;
import com.shf.gulimall.product.app.dto.ProductCopyGenerateResponse;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Captor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.MockitoJUnitRunner;

import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.Collections;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@RunWith(MockitoJUnitRunner.class)
public class ProductAiApplicationServiceTests {

    @Mock
    private ProductCopyAiService productCopyAiService;

    @InjectMocks
    private ProductAiApplicationService productAiApplicationService;

    @Captor
    private ArgumentCaptor<ProductCopyAiRequest> requestCaptor;

    @Test
    public void generateProductCopyMapsRequestToAiAdapterRequest() {
        ProductCopyGenerateRequest request = new ProductCopyGenerateRequest();
        request.setTitle("  lightweight down jacket  ");
        request.setCategory("  apparel  ");
        request.setSellingPoints(Arrays.asList(" warm ", "", null, " commute "));
        request.setTone(" Marketing ");
        request.setModelProvider(" Qwen ");
        request.setModelName(" qwen-plus ");
        request.setKnowledgeBaseId(" kb-real ");

        when(productCopyAiService.generateProductCopy(any(ProductCopyAiRequest.class))).thenReturn(buildSuccessResponse());

        ProductCopyGenerateResponse response = productAiApplicationService.generateProductCopy(request);

        verify(productCopyAiService).generateProductCopy(requestCaptor.capture());
        ProductCopyAiRequest captured = requestCaptor.getValue();
        assertEquals("lightweight down jacket", captured.getTitle());
        assertEquals("apparel", captured.getCategory());
        assertEquals(Arrays.asList("warm", "commute"), captured.getSellingPoints());
        assertEquals("marketing", captured.getTone());
        assertEquals("qwen", captured.getModelProvider());
        assertEquals("qwen-plus", captured.getModelName());
        assertEquals("kb-real", captured.getKnowledgeBaseId());
        assertTrue(response.isSuccess());
        assertEquals("rag", response.getResponse_source());
        assertEquals("mock-embedding", response.getEmbeddingProvider());
        assertEquals(1, response.getUsedChunks().size());
        assertEquals("chunk-real-0", response.getUsedChunks().get(0).getChunkId());
    }

    @Test
    public void generateProductCopyUsesDefaultToneWhenToneIsBlank() {
        ProductCopyGenerateRequest request = new ProductCopyGenerateRequest();
        request.setTitle("coffee machine");
        request.setCategory(null);
        request.setTone("   ");

        when(productCopyAiService.generateProductCopy(any(ProductCopyAiRequest.class))).thenReturn(buildSuccessResponse());

        productAiApplicationService.generateProductCopy(request);

        verify(productCopyAiService).generateProductCopy(requestCaptor.capture());
        ProductCopyAiRequest captured = requestCaptor.getValue();
        assertEquals("professional", captured.getTone());
        assertNotNull(captured.getCategory());
        assertEquals("mock", captured.getModelProvider());
        assertEquals("mock-product-copy-v1", captured.getModelName());
    }

    @Test
    public void generateProductCopyHandlesEmptySellingPoints() {
        ProductCopyGenerateRequest request = new ProductCopyGenerateRequest();
        request.setTitle("coffee machine");
        request.setSellingPoints(null);

        when(productCopyAiService.generateProductCopy(any(ProductCopyAiRequest.class))).thenReturn(buildSuccessResponse());

        productAiApplicationService.generateProductCopy(request);

        verify(productCopyAiService).generateProductCopy(requestCaptor.capture());
        ProductCopyAiRequest captured = requestCaptor.getValue();
        assertNotNull(captured.getSellingPoints());
        assertTrue(captured.getSellingPoints().isEmpty());
    }

    @Test
    public void generateProductCopyPassesThroughDegradedAdapterResponse() {
        ProductCopyGenerateRequest request = new ProductCopyGenerateRequest();
        request.setTitle("coffee machine");

        ProductCopyAiResponse degraded = new ProductCopyAiResponse();
        degraded.setGeneratedTitle("fallback title");
        degraded.setHighlights(Collections.singletonList("stable structure"));
        degraded.setSummary("remote timeout");
        degraded.setProvider("java-timeout-fallback");
        degraded.setMock(true);
        degraded.setSuccess(false);
        degraded.setMessage("remote timeout");
        degraded.setResponse_source("no_rag_fallback");

        when(productCopyAiService.generateProductCopy(any(ProductCopyAiRequest.class))).thenReturn(degraded);

        ProductCopyGenerateResponse response = productAiApplicationService.generateProductCopy(request);

        assertFalse(response.isSuccess());
        assertEquals("java-timeout-fallback", response.getProvider());
        assertEquals("remote timeout", response.getMessage());
        assertEquals("no_rag_fallback", response.getResponse_source());
    }

    @Test
    public void generateProductCopyReturnsSafeFallbackWhenAdapterThrowsException() {
        ProductCopyGenerateRequest request = new ProductCopyGenerateRequest();
        request.setTitle("coffee machine");
        request.setSellingPoints(Collections.singletonList("fast brew"));

        when(productCopyAiService.generateProductCopy(any(ProductCopyAiRequest.class)))
                .thenThrow(new IllegalStateException("boom"));

        ProductCopyGenerateResponse response = productAiApplicationService.generateProductCopy(request);

        assertFalse(response.isSuccess());
        assertTrue(response.isMock());
        assertEquals("product-ai-application-fallback", response.getProvider());
        assertEquals("no_rag_fallback", response.getResponse_source());
        assertEquals(Collections.singletonList("fast brew"), response.getHighlights());
    }

    @Test
    public void listMerchantKnowledgeBasesMapsChunkAndEmbeddingFields() {
        KnowledgeBaseOption option = new KnowledgeBaseOption();
        option.setId("kb-real");
        option.setLabel("Real Knowledge Base");
        option.setDescription("User uploaded txt knowledge base");
        option.setDocumentCount(2);
        option.setChunkCount(4);
        option.setEmbeddingStatus("embedded:mock-embedding");
        option.setUpdatedAt("2026-05-31T10:00:00Z");
        option.setSource("upload-txt");

        when(productCopyAiService.getMerchantKnowledgeBases()).thenReturn(Collections.singletonList(option));

        assertEquals(1, productAiApplicationService.listMerchantKnowledgeBases().size());
        assertEquals(4, productAiApplicationService.listMerchantKnowledgeBases().get(0).getChunkCount());
        assertEquals("upload-txt", productAiApplicationService.listMerchantKnowledgeBases().get(0).getSource());
    }

    @Test
    public void createMerchantKnowledgeBaseReturnsStructuredResponse() {
        KnowledgeBaseCreateResponse createResponse = new KnowledgeBaseCreateResponse();
        createResponse.setId("kb-real");
        createResponse.setLabel("Phone Knowledge Base");
        createResponse.setDescription("Phone selling points");
        createResponse.setEmbeddingStatus("empty");
        createResponse.setSource("manual");
        createResponse.setUpdatedAt("2026-05-31T10:10:00Z");

        when(productCopyAiService.createKnowledgeBase(any())).thenReturn(createResponse);

        MerchantKnowledgeBaseCreateResponse response =
                productAiApplicationService.createMerchantKnowledgeBase(" Phone Knowledge Base ", " Phone selling points ");

        assertEquals("kb-real", response.getId());
        assertEquals("Phone Knowledge Base", response.getLabel());
        assertEquals("empty", response.getEmbeddingStatus());
        assertEquals("manual", response.getSource());
    }

    @Test
    public void uploadTxtKnowledgeBaseMapsResponse() {
        KnowledgeBaseUploadTxtResponse uploadResponse = new KnowledgeBaseUploadTxtResponse();
        uploadResponse.setKnowledgeBaseId("kb-real");
        uploadResponse.setName("Real Knowledge Base");
        uploadResponse.setDocumentId("doc-real");
        uploadResponse.setChunkCount(3);
        uploadResponse.setEmbeddingProvider("mock-embedding");
        uploadResponse.setStatus("ready");

        when(productCopyAiService.uploadTxtKnowledgeBase(anyString(), anyString(), anyString(), any(byte[].class)))
                .thenReturn(uploadResponse);

        MerchantKnowledgeBaseUploadTxtResponse response = productAiApplicationService.uploadTxtKnowledgeBase(
                " Real Knowledge Base ",
                " Uploaded txt ",
                " real.txt ",
                "Chinese content".getBytes(StandardCharsets.UTF_8)
        );

        assertEquals("kb-real", response.getKnowledgeBaseId());
        assertEquals("doc-real", response.getDocumentId());
        assertEquals(3, response.getChunkCount());
        assertEquals("mock-embedding", response.getEmbeddingProvider());
        assertEquals("ready", response.getStatus());
        verify(productCopyAiService).uploadTxtKnowledgeBase(
                anyString(),
                anyString(),
                anyString(),
                any(byte[].class)
        );
    }

    @Test
    public void importMerchantKnowledgeBaseTextDocumentMapsDocumentPayload() {
        KnowledgeBaseDocument document = new KnowledgeBaseDocument();
        document.setId("doc-1");
        document.setKnowledgeBaseId("kb-real");
        document.setTitle("Launch Notes");
        document.setChunkCount(2);
        document.setEmbeddingStatus("embedded:mock-embedding");
        document.setUpdatedAt("2026-05-31T10:20:00Z");
        document.setContentPreview("Launch notes preview");

        when(productCopyAiService.importTextDocument(any(), any())).thenReturn(document);
        when(productCopyAiService.getKnowledgeBaseDocuments("kb-real")).thenReturn(Collections.singletonList(document));

        MerchantKnowledgeBaseDocumentResponse response =
                productAiApplicationService.importMerchantKnowledgeBaseTextDocument("kb-real", " Launch Notes ", " Text content ");

        assertEquals("doc-1", response.getId());
        assertEquals(2, response.getChunkCount());
        assertEquals("embedded:mock-embedding", response.getEmbeddingStatus());
        assertEquals(1, productAiApplicationService.listMerchantKnowledgeBaseDocuments("kb-real").size());
    }

    private ProductCopyAiResponse buildSuccessResponse() {
        ProductCopyAiResponse response = new ProductCopyAiResponse();
        response.setGeneratedTitle("RAG title");
        response.setHighlights(Arrays.asList("warm", "commute"));
        response.setSummary("RAG summary");
        response.setProvider("qwen-plus");
        response.setMock(false);
        response.setSuccess(true);
        response.setMessage("ok");
        response.setResponse_source("rag");
        response.setEmbeddingProvider("mock-embedding");

        RagUsedChunk chunk = new RagUsedChunk();
        chunk.setChunkId("chunk-real-0");
        chunk.setDocumentId("doc-real");
        chunk.setKnowledgeBaseId("kb-real");
        chunk.setContent("Chunk content from uploaded txt.");
        chunk.setSourceFilename("real.txt");
        chunk.setChunkIndex(0);
        chunk.setScore(0.92D);
        response.setUsedChunks(Collections.singletonList(chunk));
        response.setCitations(Collections.singletonList(chunk));
        return response;
    }
}
