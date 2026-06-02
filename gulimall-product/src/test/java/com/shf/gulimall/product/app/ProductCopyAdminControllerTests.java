package com.shf.gulimall.product.app;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.shf.gulimall.product.app.dto.ProductCopyGenerateRequest;
import com.shf.gulimall.product.app.dto.ProductCopyGenerateResponse;
import com.shf.gulimall.product.app.dto.RagUsedChunkResponse;
import com.shf.gulimall.product.app.service.ProductAiApplicationService;
import com.shf.gulimall.product.exception.GulimallExceptionControllerAdvice;
import org.junit.Before;
import org.junit.Test;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.validation.beanvalidation.LocalValidatorFactoryBean;

import java.util.Collections;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

public class ProductCopyAdminControllerTests {

    private MockMvc mockMvc;
    private ProductAiApplicationService productAiApplicationService;
    private ObjectMapper objectMapper;

    @Before
    public void setUp() {
        productAiApplicationService = mock(ProductAiApplicationService.class);
        ProductCopyAdminController controller = new ProductCopyAdminController(productAiApplicationService);

        LocalValidatorFactoryBean validator = new LocalValidatorFactoryBean();
        validator.afterPropertiesSet();

        mockMvc = MockMvcBuilders.standaloneSetup(controller)
                .setValidator(validator)
                .setControllerAdvice(new GulimallExceptionControllerAdvice())
                .build();
        objectMapper = new ObjectMapper();
    }

    @Test
    public void generateProductCopyReturnsStructuredSuccessPayloadWithRagFields() throws Exception {
        ProductCopyGenerateResponse response = new ProductCopyGenerateResponse();
        response.setGeneratedTitle("RAG title");
        response.setSummary("RAG summary");
        response.setProvider("qwen-plus");
        response.setMock(false);
        response.setSuccess(true);
        response.setMessage("ok");
        response.setResponse_source("rag");
        response.setEmbeddingProvider("mock-embedding");

        RagUsedChunkResponse chunk = new RagUsedChunkResponse();
        chunk.setChunkId("chunk-real-0");
        chunk.setDocumentId("doc-real");
        chunk.setKnowledgeBaseId("kb-real");
        chunk.setSourceFilename("real.txt");
        chunk.setChunkIndex(0);
        chunk.setContent("Chunk content.");
        chunk.setScore(0.91D);
        response.setUsedChunks(Collections.singletonList(chunk));
        response.setCitations(Collections.singletonList(chunk));

        when(productAiApplicationService.generateProductCopy(any(ProductCopyGenerateRequest.class))).thenReturn(response);

        ProductCopyGenerateRequest request = new ProductCopyGenerateRequest();
        request.setTitle("Coffee Machine");
        request.setCategory("appliance");
        request.setTone("marketing");
        request.setKnowledgeBaseId("kb-real");

        mockMvc.perform(post("/product/ai/product-copy/generate")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(0))
                .andExpect(jsonPath("$.msg").value("ok"))
                .andExpect(jsonPath("$.data.success").value(true))
                .andExpect(jsonPath("$.data.provider").value("qwen-plus"))
                .andExpect(jsonPath("$.data.generatedTitle").value("RAG title"))
                .andExpect(jsonPath("$.data.response_source").value("rag"))
                .andExpect(jsonPath("$.data.embeddingProvider").value("mock-embedding"))
                .andExpect(jsonPath("$.data.usedChunks[0].chunkId").value("chunk-real-0"))
                .andExpect(jsonPath("$.data.usedChunks[0].knowledgeBaseId").value("kb-real"));
    }

    @Test
    public void generateProductCopyRejectsBlankTitle() throws Exception {
        mockMvc.perform(post("/product/ai/product-copy/generate")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"title\":\"   \",\"category\":\"apparel\",\"tone\":\"marketing\"}"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.code").value(10001));
    }

    @Test
    public void generateProductCopyRejectsInvalidTone() throws Exception {
        mockMvc.perform(post("/product/ai/product-copy/generate")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"title\":\"Coffee Machine\",\"category\":\"appliance\",\"tone\":\"aggressive\"}"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.code").value(10001));
    }
}
