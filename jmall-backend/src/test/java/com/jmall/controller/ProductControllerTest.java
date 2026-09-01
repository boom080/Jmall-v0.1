package com.jmall.controller;

import com.jmall.common.R;
import com.jmall.config.LoginInterceptor;
import com.jmall.dto.PublishCheckResult;
import com.jmall.service.ProductService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.test.web.servlet.MockMvc;

import java.util.List;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(ProductController.class)
class ProductControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private ProductService productService;

    @MockBean
    private LoginInterceptor loginInterceptor;

    @BeforeEach
    void allowAuthenticatedRequest() throws Exception {
        when(loginInterceptor.preHandle(any(), any(), any())).thenReturn(true);
    }

    @Test
    void publishCheckReturnsStructuredBlockers() throws Exception {
        when(productService.publishCheck(12L)).thenReturn(R.ok(
                new PublishCheckResult(false, List.of())));

        mockMvc.perform(post("/api/products/12/publish-check"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(10000))
                .andExpect(jsonPath("$.data.publishable").value(false))
                .andExpect(jsonPath("$.data.publish_blockers").isArray());

        verify(productService).publishCheck(12L);
    }

    @Test
    void publishAndUnpublishDelegateToService() throws Exception {
        when(productService.publish(12L)).thenReturn(R.ok("published"));
        when(productService.unpublish(12L)).thenReturn(R.ok("draft"));

        mockMvc.perform(post("/api/products/12/publish"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(10000));
        mockMvc.perform(post("/api/products/12/unpublish"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(10000));

        verify(productService).publish(12L);
        verify(productService).unpublish(12L);
    }
}
