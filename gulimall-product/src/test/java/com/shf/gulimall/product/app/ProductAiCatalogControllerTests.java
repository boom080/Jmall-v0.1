package com.shf.gulimall.product.app;

import com.shf.gulimall.product.app.dto.MerchantKnowledgeBaseUploadTxtResponse;
import com.shf.gulimall.product.app.dto.ProductAiKnowledgeBaseOptionResponse;
import com.shf.gulimall.product.app.dto.ProductAiModelOptionResponse;
import com.shf.gulimall.product.app.service.ProductAiApplicationService;
import org.junit.Before;
import org.junit.Test;
import org.springframework.http.MediaType;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import java.nio.charset.StandardCharsets;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.multipart;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

public class ProductAiCatalogControllerTests {

    private MockMvc mockMvc;
    private ProductAiApplicationService productAiApplicationService;

    @Before
    public void setUp() {
        productAiApplicationService = mock(ProductAiApplicationService.class);
        ProductAiCatalogController controller = new ProductAiCatalogController(productAiApplicationService);
        mockMvc = MockMvcBuilders.standaloneSetup(controller).build();
    }

    @Test
    public void listModelsReturnsStructuredPayload() throws Exception {
        ProductAiModelOptionResponse option = new ProductAiModelOptionResponse();
        option.setId("mock:mock-product-copy-v1");
        option.setLabel("Mock / mock-product-copy-v1");
        option.setProvider("mock");
        option.setModelName("mock-product-copy-v1");

        when(productAiApplicationService.listAvailableModels()).thenReturn(java.util.Collections.singletonList(option));

        mockMvc.perform(get("/product/ai/models"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(0))
                .andExpect(jsonPath("$.data[0].provider").value("mock"))
                .andExpect(jsonPath("$.data[0].modelName").value("mock-product-copy-v1"));
    }

    @Test
    public void listKnowledgeBasesReturnsStructuredPayload() throws Exception {
        ProductAiKnowledgeBaseOptionResponse option = new ProductAiKnowledgeBaseOptionResponse();
        option.setId("kb-real");
        option.setLabel("Real Knowledge Base");
        option.setDocumentCount(2);
        option.setChunkCount(5);
        option.setSource("upload-txt");

        when(productAiApplicationService.listKnowledgeBases()).thenReturn(java.util.Collections.singletonList(option));

        mockMvc.perform(get("/product/ai/knowledge-bases"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(0))
                .andExpect(jsonPath("$.data[0].id").value("kb-real"))
                .andExpect(jsonPath("$.data[0].documentCount").value(2))
                .andExpect(jsonPath("$.data[0].chunkCount").value(5))
                .andExpect(jsonPath("$.data[0].source").value("upload-txt"));
    }

    @Test
    public void uploadTxtKnowledgeBaseAcceptsMultipartAndReturnsStructuredPayload() throws Exception {
        MerchantKnowledgeBaseUploadTxtResponse response = new MerchantKnowledgeBaseUploadTxtResponse();
        response.setKnowledgeBaseId("kb-real");
        response.setName("Real Knowledge Base");
        response.setDocumentId("doc-real");
        response.setChunkCount(3);
        response.setEmbeddingProvider("mock-embedding");
        response.setStatus("ready");

        when(productAiApplicationService.uploadTxtKnowledgeBase(
                anyString(),
                anyString(),
                anyString(),
                any(byte[].class)
        )).thenReturn(response);

        MockMultipartFile file = new MockMultipartFile(
                "file",
                "real.txt",
                "text/plain",
                "real txt content".getBytes(StandardCharsets.UTF_8)
        );

        mockMvc.perform(multipart("/product/ai/knowledge-bases/upload-txt")
                        .file(file)
                        .param("name", "Real Knowledge Base")
                        .param("description", "Uploaded txt")
                        .contentType(MediaType.MULTIPART_FORM_DATA))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(0))
                .andExpect(jsonPath("$.data.knowledgeBaseId").value("kb-real"))
                .andExpect(jsonPath("$.data.documentId").value("doc-real"))
                .andExpect(jsonPath("$.data.chunkCount").value(3))
                .andExpect(jsonPath("$.data.embeddingProvider").value("mock-embedding"))
                .andExpect(jsonPath("$.data.status").value("ready"));
    }
}
