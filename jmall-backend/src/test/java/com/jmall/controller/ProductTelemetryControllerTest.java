package com.jmall.controller;

import com.jmall.common.UserContext;
import com.jmall.config.LoginInterceptor;
import com.jmall.dto.EditorEventStage;
import com.jmall.service.ProductMetrics;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.MockedStatic;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import java.util.UUID;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mockStatic;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(ProductTelemetryController.class)
class ProductTelemetryControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private ProductMetrics productMetrics;

    @MockBean
    private LoginInterceptor loginInterceptor;

    private MockedStatic<UserContext> userContext;

    @BeforeEach
    void setUp() throws Exception {
        userContext = mockStatic(UserContext.class);
        userContext.when(UserContext::getUserId).thenReturn(7L);
        when(loginInterceptor.preHandle(any(), any(), any())).thenReturn(true);
    }

    @AfterEach
    void tearDown() {
        userContext.close();
    }

    @Test
    void acceptsAuthenticatedEditorEventAndReturnsDedupResult() throws Exception {
        UUID sessionId = UUID.randomUUID();
        when(productMetrics.recordEditorEvent(sessionId, EditorEventStage.EDITOR_OPENED)).thenReturn(true);

        mockMvc.perform(post("/api/telemetry/editor-events")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"sessionId\":\"" + sessionId
                                + "\",\"stage\":\"editor_opened\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(10000))
                .andExpect(jsonPath("$.data.recorded").value(true));

        verify(productMetrics).recordEditorEvent(sessionId, EditorEventStage.EDITOR_OPENED);
    }

    @Test
    void rejectsInvalidUuidAndStageAsBadRequest() throws Exception {
        mockMvc.perform(post("/api/telemetry/editor-events")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"sessionId\":\"not-a-uuid\",\"stage\":\"editor_opened\"}"))
                .andExpect(status().isBadRequest());

        mockMvc.perform(post("/api/telemetry/editor-events")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"sessionId\":\"" + UUID.randomUUID()
                                + "\",\"stage\":\"unknown\"}"))
                .andExpect(status().isBadRequest());
    }

    @Test
    void rejectsMissingUserContext() throws Exception {
        userContext.when(UserContext::getUserId).thenReturn(null);

        mockMvc.perform(post("/api/telemetry/editor-events")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"sessionId\":\"" + UUID.randomUUID()
                                + "\",\"stage\":\"editor_opened\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(10010));
    }
}
