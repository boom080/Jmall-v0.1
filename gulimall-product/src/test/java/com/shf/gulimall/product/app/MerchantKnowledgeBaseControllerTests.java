package com.shf.gulimall.product.app;

import com.shf.gulimall.product.app.dto.MerchantKnowledgeBaseCreateResponse;
import com.shf.gulimall.product.app.dto.MerchantKnowledgeBaseDocumentResponse;
import com.shf.gulimall.product.app.dto.ProductAiKnowledgeBaseOptionResponse;
import com.shf.gulimall.product.app.service.ProductAiApplicationService;
import org.junit.Before;
import org.junit.Test;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import java.util.Collections;

import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

public class MerchantKnowledgeBaseControllerTests {

    private MockMvc mockMvc;
    private ProductAiApplicationService productAiApplicationService;

    @Before
    public void setUp() {
        productAiApplicationService = mock(ProductAiApplicationService.class);
        MerchantKnowledgeBaseController controller = new MerchantKnowledgeBaseController(productAiApplicationService);
        mockMvc = MockMvcBuilders.standaloneSetup(controller).build();
    }

    @Test
    public void listKnowledgeBasesReturnsStructuredPayload() throws Exception {
        ProductAiKnowledgeBaseOptionResponse response = new ProductAiKnowledgeBaseOptionResponse();
        response.setId("kb-demo");
        response.setLabel("手机知识库");
        response.setDocumentCount(1);
        response.setChunkCount(2);
        response.setEmbeddingStatus("embedded:mock-embedding");

        when(productAiApplicationService.listMerchantKnowledgeBases())
                .thenReturn(Collections.singletonList(response));

        mockMvc.perform(get("/product/merchant/knowledge-bases"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(0))
                .andExpect(jsonPath("$.data[0].id").value("kb-demo"))
                .andExpect(jsonPath("$.data[0].chunkCount").value(2));
    }

    @Test
    public void createKnowledgeBaseReturnsStructuredPayload() throws Exception {
        MerchantKnowledgeBaseCreateResponse response = new MerchantKnowledgeBaseCreateResponse();
        response.setId("kb-demo");
        response.setLabel("手机知识库");
        response.setEmbeddingStatus("empty");

        when(productAiApplicationService.createMerchantKnowledgeBase(anyString(), anyString()))
                .thenReturn(response);

        mockMvc.perform(
                        post("/product/merchant/knowledge-bases")
                                .contentType("application/json")
                                .content("{\"name\":\"手机知识库\",\"description\":\"用于手机卖点\"}")
                )
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(0))
                .andExpect(jsonPath("$.data.id").value("kb-demo"))
                .andExpect(jsonPath("$.data.embeddingStatus").value("empty"));
    }

    @Test
    public void importTextDocumentReturnsStructuredPayload() throws Exception {
        MerchantKnowledgeBaseDocumentResponse response = new MerchantKnowledgeBaseDocumentResponse();
        response.setId("doc-1");
        response.setKnowledgeBaseId("kb-demo");
        response.setTitle("新品卖点");
        response.setChunkCount(2);
        response.setEmbeddingStatus("embedded:mock-embedding");

        when(productAiApplicationService.importMerchantKnowledgeBaseTextDocument(anyString(), anyString(), anyString()))
                .thenReturn(response);

        mockMvc.perform(
                        post("/product/merchant/knowledge-bases/kb-demo/documents/text")
                                .contentType("application/json")
                                .content("{\"title\":\"新品卖点\",\"content\":\"Jrun X1 主打长续航与轻办公场景。\"}")
                )
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(0))
                .andExpect(jsonPath("$.data.id").value("doc-1"))
                .andExpect(jsonPath("$.data.chunkCount").value(2));
    }

    @Test
    public void importPdfDocumentReturnsStructuredPayload() throws Exception {
        MerchantKnowledgeBaseDocumentResponse response = new MerchantKnowledgeBaseDocumentResponse();
        response.setId("doc-pdf");
        response.setKnowledgeBaseId("kb-demo");
        response.setTitle("PDF 卖点");
        response.setChunkCount(3);
        response.setEmbeddingStatus("embedded:mock-embedding");

        when(productAiApplicationService.importMerchantKnowledgeBasePdfDocument(anyString(), anyString(), anyString(), org.mockito.ArgumentMatchers.any(byte[].class)))
                .thenReturn(response);

        MockMultipartFile file = new MockMultipartFile(
                "file",
                "demo.pdf",
                "application/pdf",
                "%PDF-1.4 demo".getBytes(java.nio.charset.StandardCharsets.UTF_8)
        );

        mockMvc.perform(
                        org.springframework.test.web.servlet.request.MockMvcRequestBuilders.multipart("/product/merchant/knowledge-bases/kb-demo/documents/pdf")
                                .file(file)
                                .param("title", "PDF 卖点")
                                .contentType(MediaType.MULTIPART_FORM_DATA)
                )
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(0))
                .andExpect(jsonPath("$.data.id").value("doc-pdf"))
                .andExpect(jsonPath("$.data.chunkCount").value(3));
    }

    @Test
    public void listDocumentsReturnsStructuredPayload() throws Exception {
        MerchantKnowledgeBaseDocumentResponse response = new MerchantKnowledgeBaseDocumentResponse();
        response.setId("doc-1");
        response.setKnowledgeBaseId("kb-demo");
        response.setTitle("新品卖点");
        response.setChunkCount(2);
        response.setEmbeddingStatus("embedded:mock-embedding");

        when(productAiApplicationService.listMerchantKnowledgeBaseDocuments("kb-demo"))
                .thenReturn(Collections.singletonList(response));

        mockMvc.perform(get("/product/merchant/knowledge-bases/kb-demo/documents"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(0))
                .andExpect(jsonPath("$.data[0].title").value("新品卖点"));
    }
}





