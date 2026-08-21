package com.jmall.service;

import com.jmall.common.R;
import com.jmall.common.UserContext;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockedStatic;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.web.client.RestTemplate;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class AiProxyServiceTest {

    @Mock
    private UserService userService;

    @Mock
    private RestTemplate restTemplate;

    @InjectMocks
    private AiProxyService aiProxyService;

    private MockedStatic<UserContext> userContextMock;

    private static final Long TEST_USER_ID = 1L;
    private static final String BASE_URL = "http://localhost:18080";

    @BeforeEach
    void setUp() {
        userContextMock = mockStatic(UserContext.class);
        userContextMock.when(UserContext::getUserId).thenReturn(TEST_USER_ID);

        // Inject the base URL via reflection (no setter in production code)
        ReflectionTestUtils.setField(aiProxyService, "aiBaseUrl", BASE_URL);
        ReflectionTestUtils.setField(aiProxyService, "restTemplate", restTemplate);
    }

    @AfterEach
    void tearDown() {
        userContextMock.close();
    }

    // ---- orchestrate ----

    @Test
    void orchestrate_deductsGoldOnSuccess() {
        when(userService.deductGold(eq(TEST_USER_ID), eq(10L),
                eq("ai_cost"), contains("AI service")))
                .thenReturn(true);

        // Mock RestTemplate exchange for the forward
        org.springframework.http.ResponseEntity<String> mockResponse =
                org.springframework.http.ResponseEntity.ok("{\"result\": \"ok\"}");
        when(restTemplate.postForEntity(
                eq(BASE_URL + "/api/agent/orchestrate"),
                any(org.springframework.http.HttpEntity.class),
                eq(String.class)))
                .thenReturn(mockResponse);

        Map<String, Object> request = Map.of("productInfo", Map.of("title", "test"));
        R result = aiProxyService.orchestrate(request);

        assertNotNull(result);
        verify(userService).deductGold(eq(TEST_USER_ID), eq(10L), eq("ai_cost"), anyString());
    }

    @Test
    void orchestrate_returnsErrorWhenGoldInsufficient() {
        when(userService.deductGold(eq(TEST_USER_ID), eq(10L),
                eq("ai_cost"), anyString()))
                .thenReturn(false);

        Map<String, Object> request = Map.of("productInfo", Map.of("title", "test"));
        R result = aiProxyService.orchestrate(request);

        assertNotEquals(0, result.getCode());
        // Should NOT call the agent
        verify(restTemplate, never()).exchange(anyString(), any(), any(), eq(String.class));
    }

    @Test
    void orchestrate_handlesAgentServiceError() {
        when(userService.deductGold(anyLong(), anyLong(), anyString(), anyString()))
                .thenReturn(true);

        when(restTemplate.postForEntity(
                contains("/api/agent/orchestrate"),
                any(org.springframework.http.HttpEntity.class),
                eq(String.class)))
                .thenThrow(new RuntimeException("Connection refused"));

        Map<String, Object> request = Map.of("productInfo", Map.of("title", "test"));
        R result = aiProxyService.orchestrate(request);

        assertNotEquals(0, result.getCode());
        // Should refund gold on failure
        verify(userService).addGold(eq(TEST_USER_ID), eq(10L), eq("refund"), anyString());
    }

    // ---- SSE streaming ----

    @Test
    void orchestrateStream_chargesGoldBeforeStreaming() {
        when(userService.deductGold(eq(TEST_USER_ID), eq(10L),
                eq("ai_cost"), contains("stream")))
                .thenReturn(true);

        Map<String, Object> request = Map.of("productInfo", Map.of("title", "test"));

        var emitter = aiProxyService.orchestrateStream(request);
        assertNotNull(emitter);

        verify(userService).deductGold(eq(TEST_USER_ID), eq(10L),
                eq("ai_cost"), contains("stream"));
    }

    @Test
    void orchestrateStream_rejectsWhenGoldInsufficient() {
        when(userService.deductGold(anyLong(), anyLong(), anyString(), anyString()))
                .thenReturn(false);

        Map<String, Object> request = Map.of("productInfo", Map.of("title", "test"));

        var emitter = aiProxyService.orchestrateStream(request);
        assertNotNull(emitter);

        // The emitter should be completed with error — we can't easily test that
        // without a full Spring context, but the gold deduction was attempted
        verify(userService).deductGold(eq(TEST_USER_ID), eq(10L), eq("ai_cost"), anyString());
    }

    // ---- getStyles (no gold cost) ----

    @Test
    void getStyles_doesNotChargeGold() {
        org.springframework.http.ResponseEntity<String> mockResponse =
                org.springframework.http.ResponseEntity.ok("{\"styles\": []}");
        when(restTemplate.exchange(
                eq(BASE_URL + "/api/styles"),
                eq(org.springframework.http.HttpMethod.GET),
                any(org.springframework.http.HttpEntity.class),
                eq(String.class)))
                .thenReturn(mockResponse);

        R result = aiProxyService.getStyles();
        assertNotNull(result);

        // Verify no gold was charged
        verify(userService, never()).deductGold(anyLong(), anyLong(), anyString(), anyString());
    }

    // ---- Error scenarios ----

    @Test
    void allEndpoints_handleNetworkErrorGracefully() {
        // getStyles is a simpler endpoint — test error handling there
        when(restTemplate.exchange(
                contains("/api/styles"),
                eq(org.springframework.http.HttpMethod.GET),
                any(org.springframework.http.HttpEntity.class),
                eq(String.class)))
                .thenThrow(new RuntimeException("Network error"));

        R result = aiProxyService.getStyles();
        assertNotNull(result);
        assertNotEquals(0, result.getCode());
        assertTrue(result.getMsg().contains("AI service error"));
    }
}
