package com.jmall.controller;

import com.jmall.common.R;
import com.jmall.common.UserContext;
import com.jmall.service.AiProxyService;
import com.jmall.config.LoginInterceptor;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.MockedStatic;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import java.util.Map;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyMap;
import static org.mockito.Mockito.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/**
 * Controller-layer tests for AiProxyController.
 *
 * Uses Spring MockMvc with @WebMvcTest for focused controller testing.
 */
@WebMvcTest(AiProxyController.class)
class AiProxyControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private AiProxyService aiProxyService;

    @MockBean
    private LoginInterceptor loginInterceptor;

    private MockedStatic<UserContext> userContextMock;

    @BeforeEach
    void setUp() {
        userContextMock = mockStatic(UserContext.class);
        // Simulate authenticated user
        userContextMock.when(UserContext::getUserId).thenReturn(1L);
        try {
            when(loginInterceptor.preHandle(any(), any(), any())).thenReturn(true);
        } catch (Exception exception) {
            throw new RuntimeException(exception);
        }
    }

    @AfterEach
    void tearDown() {
        userContextMock.close();
    }

    // ---- POST /api/ai/orchestrate ----

    @Test
    void orchestrate_returnsJson() throws Exception {
        when(aiProxyService.orchestrate(anyMap()))
                .thenReturn(R.ok("AI service response", "{\"result\":\"ok\"}"));

        mockMvc.perform(post("/api/ai/orchestrate")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                            {
                                "productInfo": {
                                    "title": "测试商品",
                                    "category": "测试"
                                },
                                "targetStyle": "taobao"
                            }
                            """))
                .andExpect(status().isOk())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.code").value(10000));

        verify(aiProxyService).orchestrate(anyMap());
    }

    @Test
    void orchestrate_passesAllFields() throws Exception {
        when(aiProxyService.orchestrate(anyMap()))
                .thenReturn(R.ok("ok"));

        mockMvc.perform(post("/api/ai/orchestrate")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                            {
                                "productInfo": {
                                    "title": "静音破壁机",
                                    "category": "厨房电器",
                                    "description": "高品质",
                                    "price": "29900"
                                },
                                "targetStyle": "pinduoduo"
                            }
                            """))
                .andExpect(status().isOk());

        verify(aiProxyService).orchestrate(anyMap());
    }

    // ---- POST /api/ai/orchestrate/stream (SSE) ----

    @Test
    void orchestrateStream_returnsSseEventStream() throws Exception {
        org.springframework.web.servlet.mvc.method.annotation.SseEmitter emitter =
                new org.springframework.web.servlet.mvc.method.annotation.SseEmitter();
        when(aiProxyService.orchestrateStream(anyMap())).thenReturn(emitter);

        mockMvc.perform(post("/api/ai/orchestrate/stream")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                            {
                                "productInfo": {
                                    "title": "测试",
                                    "category": "测试"
                                },
                                "targetStyle": "taobao"
                            }
                            """))
                .andExpect(status().isOk());

        verify(aiProxyService).orchestrateStream(anyMap());
    }

    // ---- POST /api/ai/product/copy ----

    @Test
    void productCopy_returnsJson() throws Exception {
        when(aiProxyService.generateProductCopy(anyLong(), anyString()))
                .thenReturn(R.ok("copy generated"));

        mockMvc.perform(post("/api/ai/product/copy")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                            {
                                "productId": 1,
                                "style": "jd"
                            }
                            """))
                .andExpect(status().isOk());

        verify(aiProxyService).generateProductCopy(1L, "jd");
    }

    // ---- POST /api/ai/product/review ----

    @Test
    void productReview_returnsJson() throws Exception {
        when(aiProxyService.reviewProduct(anyLong()))
                .thenReturn(R.ok("review complete"));

        mockMvc.perform(post("/api/ai/product/review")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"productId\": 42}"))
                .andExpect(status().isOk());

        verify(aiProxyService).reviewProduct(42L);
    }

    // ---- GET /api/ai/styles ----

    @Test
    void getStyles_returnsStyleList() throws Exception {
        when(aiProxyService.getStyles())
                .thenReturn(R.ok(Map.of("styles", java.util.List.of())));

        mockMvc.perform(get("/api/ai/styles"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(10000));

        verify(aiProxyService).getStyles();
    }

    // ---- GET /api/ai/knowledge-bases ----

    @Test
    void getKnowledgeBases_returnsList() throws Exception {
        when(aiProxyService.getKnowledgeBases())
                .thenReturn(R.ok(java.util.List.of()));

        mockMvc.perform(get("/api/ai/knowledge-bases"))
                .andExpect(status().isOk());

        verify(aiProxyService).getKnowledgeBases();
    }

    @Test
    void importKnowledgeBaseText_acceptsStringKnowledgeBaseId() throws Exception {
        when(aiProxyService.importKnowledgeBaseText(anyString(), anyString(), anyString()))
                .thenReturn(R.ok(Map.of("id", "doc-1")));

        mockMvc.perform(post("/api/ai/knowledge-bases/upload-txt")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                            {
                                "kbId": "kb-d9544b5e8cba",
                                "title": "卖点说明",
                                "content": "第一段产品资料。"
                            }
                            """))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(10000));

        verify(aiProxyService).importKnowledgeBaseText(
                "kb-d9544b5e8cba", "卖点说明", "第一段产品资料。");
    }

    // ---- GET /api/ai/admin/cost-stats ----

    @Test
    void getCostStats_returnsStats() throws Exception {
        when(aiProxyService.getCostStats())
                .thenReturn(R.ok(Map.of("daily_cost_usd", 0.5)));

        mockMvc.perform(get("/api/ai/admin/cost-stats"))
                .andExpect(status().isOk());

        verify(aiProxyService).getCostStats();
    }
}
