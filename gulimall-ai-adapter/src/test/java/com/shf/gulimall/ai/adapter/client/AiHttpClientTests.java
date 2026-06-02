package com.shf.gulimall.ai.adapter.client;

import com.shf.gulimall.ai.adapter.config.AiAdapterProperties;
import com.shf.gulimall.ai.adapter.model.AiModelOption;
import com.shf.gulimall.ai.adapter.model.KnowledgeBaseDocument;
import com.shf.gulimall.ai.adapter.model.KnowledgeBaseOption;
import com.shf.gulimall.ai.adapter.model.KnowledgeBaseUploadTxtResponse;
import com.shf.gulimall.ai.adapter.model.ProductCopyAiRequest;
import com.shf.gulimall.ai.adapter.model.ProductCopyAiResponse;
import org.junit.Test;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestTemplate;

import java.net.SocketTimeoutException;
import java.util.Arrays;
import java.util.List;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.method;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withServerError;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess;

public class AiHttpClientTests {

    @Test
    public void generateProductCopyUsesConfiguredGenerateEndpoint() {
        RestTemplate restTemplate = new RestTemplate();
        MockRestServiceServer server = MockRestServiceServer.bindTo(restTemplate).build();

        AiAdapterProperties properties = new AiAdapterProperties();
        properties.setBaseUrl("http://127.0.0.1:18080/");
        properties.setProductCopyPath("/api/product-copy/generate");

        server.expect(requestTo("http://127.0.0.1:18080/api/product-copy/generate"))
                .andExpect(method(HttpMethod.POST))
                .andRespond(withSuccess(
                        "{\"generatedTitle\":\"爆款推荐 | 轻薄羽绒服 | 服饰\",\"highlights\":[\"轻量保暖\",\"城市通勤\"],\"summary\":\"Mock summary\",\"pendingMerchantConfirmations\":[\"请商家确认保修信息。\"],\"provider\":\"mock-product-copy-v1\",\"mock\":true,\"success\":true,\"message\":\"商品文案生成成功（Mock）\"}",
                        MediaType.APPLICATION_JSON
                ));

        AiHttpClient client = new AiHttpClient(restTemplate, properties);
        ProductCopyAiRequest request = new ProductCopyAiRequest();
        request.setTitle("轻薄羽绒服");
        request.setCategory("服饰");
        request.setSellingPoints(Arrays.asList("轻量保暖", "城市通勤"));
        request.setTone("marketing");

        ProductCopyAiResponse response = client.generateProductCopy(request);

        assertEquals("爆款推荐 | 轻薄羽绒服 | 服饰", response.getGeneratedTitle());
        assertEquals("mock-product-copy-v1", response.getProvider());
        assertTrue(response.isMock());
        assertTrue(response.isSuccess());
        assertEquals("商品文案生成成功（Mock）", response.getMessage());
        assertEquals("请商家确认保修信息。", response.getPendingMerchantConfirmations().get(0));
        server.verify();
    }

    @Test
    public void generateProductCopyReturnsFallbackWhenRemoteServiceRespondsWithServerError() {
        RestTemplate restTemplate = new RestTemplate();
        MockRestServiceServer server = MockRestServiceServer.bindTo(restTemplate).build();

        AiAdapterProperties properties = new AiAdapterProperties();
        properties.setBaseUrl("http://127.0.0.1:18080");
        properties.setProductCopyPath("/api/product-copy/generate");

        server.expect(requestTo("http://127.0.0.1:18080/api/product-copy/generate"))
                .andExpect(method(HttpMethod.POST))
                .andRespond(withServerError());

        AiHttpClient client = new AiHttpClient(restTemplate, properties);
        ProductCopyAiRequest request = new ProductCopyAiRequest();
        request.setTitle("轻薄羽绒服");
        request.setCategory("服饰");
        request.setSellingPoints(Arrays.asList("轻量保暖", "城市通勤"));
        request.setTone("marketing");

        ProductCopyAiResponse response = client.generateProductCopy(request);

        assertFalse(response.isSuccess());
        assertTrue(response.isMock());
        assertEquals("java-http-status-fallback", response.getProvider());
        assertTrue(response.getMessage().contains("AI 服务响应异常"));
        server.verify();
    }

    @Test
    public void generateProductCopyReturnsFallbackWhenRequestTimesOut() {
        RestTemplate restTemplate = new RestTemplate();
        MockRestServiceServer server = MockRestServiceServer.bindTo(restTemplate).build();

        AiAdapterProperties properties = new AiAdapterProperties();
        properties.setBaseUrl("http://127.0.0.1:18080");
        properties.setProductCopyPath("/api/product-copy/generate");

        server.expect(requestTo("http://127.0.0.1:18080/api/product-copy/generate"))
                .andExpect(method(HttpMethod.POST))
                .andRespond(request -> {
                    throw new ResourceAccessException("Read timed out", new SocketTimeoutException("Read timed out"));
                });

        AiHttpClient client = new AiHttpClient(restTemplate, properties);
        ProductCopyAiRequest request = new ProductCopyAiRequest();
        request.setTitle("轻薄羽绒服");
        request.setCategory("服饰");
        request.setSellingPoints(Arrays.asList("轻量保暖", "城市通勤"));
        request.setTone("marketing");

        ProductCopyAiResponse response = client.generateProductCopy(request);

        assertFalse(response.isSuccess());
        assertTrue(response.isMock());
        assertEquals("java-timeout-fallback", response.getProvider());
        assertEquals("AI 服务调用超时，已返回降级文案。", response.getMessage());
        server.verify();
    }

    @Test
    public void getAvailableModelsUsesConfiguredEndpoint() {
        RestTemplate restTemplate = new RestTemplate();
        MockRestServiceServer server = MockRestServiceServer.bindTo(restTemplate).build();

        AiAdapterProperties properties = new AiAdapterProperties();
        properties.setBaseUrl("http://127.0.0.1:18080");
        properties.setModelsPath("/api/models");

        server.expect(requestTo("http://127.0.0.1:18080/api/models"))
                .andExpect(method(HttpMethod.GET))
                .andRespond(withSuccess(
                        "[{\"id\":\"mock:mock-product-copy-v1\",\"label\":\"Mock / mock-product-copy-v1\",\"provider\":\"mock\",\"modelName\":\"mock-product-copy-v1\",\"description\":\"mock\"}]",
                        MediaType.APPLICATION_JSON
                ));

        AiHttpClient client = new AiHttpClient(restTemplate, properties);
        List<AiModelOption> models = client.getAvailableModels();

        assertEquals(1, models.size());
        assertEquals("mock", models.get(0).getProvider());
        server.verify();
    }

    @Test
    public void getKnowledgeBasesReturnsEmptyWhenRemoteFails() {
        RestTemplate restTemplate = new RestTemplate();
        MockRestServiceServer server = MockRestServiceServer.bindTo(restTemplate).build();

        AiAdapterProperties properties = new AiAdapterProperties();
        properties.setBaseUrl("http://127.0.0.1:18080");
        properties.setKnowledgeBasesPath("/api/knowledge-bases");

        server.expect(requestTo("http://127.0.0.1:18080/api/knowledge-bases"))
                .andExpect(method(HttpMethod.GET))
                .andRespond(withServerError());

        AiHttpClient client = new AiHttpClient(restTemplate, properties);
        List<KnowledgeBaseOption> knowledgeBases = client.getKnowledgeBases();

        assertTrue(knowledgeBases.isEmpty());
        server.verify();
    }

    @Test
    public void importPdfDocumentUsesMultipartEndpoint() {
        RestTemplate restTemplate = new RestTemplate();
        MockRestServiceServer server = MockRestServiceServer.bindTo(restTemplate).build();

        AiAdapterProperties properties = new AiAdapterProperties();
        properties.setBaseUrl("http://127.0.0.1:18080");
        properties.setMerchantKnowledgeBasesPath("/api/merchant/knowledge-bases");

        server.expect(requestTo("http://127.0.0.1:18080/api/merchant/knowledge-bases/kb-demo/documents/pdf"))
                .andExpect(method(HttpMethod.POST))
                .andRespond(withSuccess(
                        "{\"id\":\"doc-pdf\",\"knowledgeBaseId\":\"kb-demo\",\"title\":\"PDF 卖点\",\"chunkCount\":3,\"embeddingStatus\":\"embedded:mock-embedding\"}",
                        MediaType.APPLICATION_JSON
                ));

        AiHttpClient client = new AiHttpClient(restTemplate, properties);
        KnowledgeBaseDocument document = client.importPdfDocument(
                "kb-demo",
                "PDF 卖点",
                "demo.pdf",
                "%PDF-1.4 demo".getBytes(java.nio.charset.StandardCharsets.UTF_8)
        );

        assertEquals("doc-pdf", document.getId());
        assertEquals(3, document.getChunkCount());
        server.verify();
    }

    @Test
    public void uploadTxtKnowledgeBaseUsesMultipartEndpoint() {
        RestTemplate restTemplate = new RestTemplate();
        MockRestServiceServer server = MockRestServiceServer.bindTo(restTemplate).build();

        AiAdapterProperties properties = new AiAdapterProperties();
        properties.setBaseUrl("http://127.0.0.1:18080");
        properties.setMerchantKnowledgeBasesPath("/api/merchant/knowledge-bases");

        server.expect(requestTo("http://127.0.0.1:18080/api/merchant/knowledge-bases/upload-txt"))
                .andExpect(method(HttpMethod.POST))
                .andRespond(withSuccess(
                        "{\"knowledgeBaseId\":\"kb-real\",\"name\":\"真实知识库\",\"documentId\":\"doc-real\",\"chunkCount\":2,\"embeddingProvider\":\"mock-embedding\",\"status\":\"ready\"}",
                        MediaType.APPLICATION_JSON
                ));

        AiHttpClient client = new AiHttpClient(restTemplate, properties);
        KnowledgeBaseUploadTxtResponse response = client.uploadTxtKnowledgeBase(
                "真实知识库",
                "txt 上传",
                "demo.txt",
                "中文资料".getBytes(java.nio.charset.StandardCharsets.UTF_8)
        );

        assertEquals("kb-real", response.getKnowledgeBaseId());
        assertEquals("doc-real", response.getDocumentId());
        assertEquals(2, response.getChunkCount());
        server.verify();
    }
}





