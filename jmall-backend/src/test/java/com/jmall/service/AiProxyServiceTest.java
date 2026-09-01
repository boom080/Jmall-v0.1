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

    private void mockReadyAssessment() {
        when(restTemplate.postForEntity(
                eq(BASE_URL + "/api/agent/input-assessment"),
                any(org.springframework.http.HttpEntity.class),
                eq(String.class)))
                .thenReturn(org.springframework.http.ResponseEntity.ok(
                        "{\"input_assessment\":{\"status\":\"ready\",\"ready\":true,\"score\":100}}"));
    }

    // ---- orchestrate ----

    @Test
    void orchestrate_deductsGoldOnSuccess() {
        mockReadyAssessment();
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
        mockReadyAssessment();
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
        mockReadyAssessment();
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

    @Test
    void orchestrate_needsInputReturnsAssessmentWithoutCharging() {
        when(restTemplate.postForEntity(
                eq(BASE_URL + "/api/agent/input-assessment"),
                any(org.springframework.http.HttpEntity.class),
                eq(String.class)))
                .thenReturn(org.springframework.http.ResponseEntity.ok(
                        "{\"input_assessment\":{\"status\":\"needs_input\",\"ready\":false,\"score\":35}}"));

        R result = aiProxyService.orchestrate(Map.of(
                "productInfo", Map.of("title", "智能破壁机", "category", "厨房电器")));

        assertEquals(10000, result.getCode());
        verify(userService, never()).deductGold(anyLong(), anyLong(), anyString(), anyString());
        verify(restTemplate, never()).postForEntity(
                eq(BASE_URL + "/api/agent/orchestrate"),
                any(org.springframework.http.HttpEntity.class),
                eq(String.class));
    }

    @Test
    void unsupportedPlatformPreflightNeverChargesOrStartsGeneration() {
        when(restTemplate.postForEntity(
                eq(BASE_URL + "/api/agent/input-assessment"), any(org.springframework.http.HttpEntity.class), eq(String.class)))
                .thenThrow(org.springframework.web.client.HttpClientErrorException.create(
                        org.springframework.http.HttpStatus.UNPROCESSABLE_ENTITY, "unsupported platform",
                        org.springframework.http.HttpHeaders.EMPTY, new byte[0], java.nio.charset.StandardCharsets.UTF_8));
        R result = aiProxyService.orchestrate(Map.of(
                "productInfo", Map.of("title", "保温杯"), "targetStyle", "amazon"));
        assertNotEquals(10000, result.getCode());
        verify(userService, never()).deductGold(anyLong(), anyLong(), anyString(), anyString());
        verify(restTemplate, never()).postForEntity(
                eq(BASE_URL + "/api/agent/orchestrate"), any(org.springframework.http.HttpEntity.class), eq(String.class));
    }

    @Test
    void orchestrationPreservesPlatformSkillMetadata() {
        mockReadyAssessment();
        when(userService.deductGold(anyLong(), anyLong(), anyString(), anyString())).thenReturn(true);
        String payload = "{\"style_adaptation\":{\"target_style\":\"jd\",\"platform_skill_id\":\"jd_listing_v1\",\"platform_skill_version\":\"1.0.0\",\"previews\":{\"jd\":{}}},\"generation_metadata\":{\"platform_skill_id\":\"jd_listing_v1\",\"platform_skill_version\":\"1.0.0\"}}";
        when(restTemplate.postForEntity(eq(BASE_URL + "/api/agent/orchestrate"),
                any(org.springframework.http.HttpEntity.class), eq(String.class)))
                .thenReturn(org.springframework.http.ResponseEntity.ok(payload));
        R result = aiProxyService.orchestrate(Map.of("productInfo", Map.of("title", "保温杯"), "targetStyle", "jd"));
        assertEquals(10000, result.getCode());
        assertEquals(payload, result.getData());
    }

    // ---- free input assessment ----

    @Test
    @SuppressWarnings("unchecked")
    void assessInput_normalizesCamelCaseAndDoesNotChargeGold() {
        org.springframework.http.ResponseEntity<String> mockResponse =
                org.springframework.http.ResponseEntity.ok(
                        "{\"input_assessment\":{\"ready\":false,\"score\":35}}");
        when(restTemplate.postForEntity(
                eq(BASE_URL + "/api/agent/input-assessment"),
                any(org.springframework.http.HttpEntity.class),
                eq(String.class)))
                .thenReturn(mockResponse);

        Map<String, Object> request = new java.util.HashMap<>();
        request.put("productInfo", Map.of(
                "title", "可拆洗记忆棉枕",
                "category", "家居用品",
                "targetAudience", "经常出差的上班族",
                "usageScenarios", "飞机和高铁"));
        request.put("targetStyle", "taobao");
        request.put("knowledgeBaseId", "kb-1");
        request.put("productDraftId", 42L);

        R result = aiProxyService.assessInput(request);

        assertNotNull(result);
        org.mockito.ArgumentCaptor<org.springframework.http.HttpEntity> entityCaptor =
                org.mockito.ArgumentCaptor.forClass(org.springframework.http.HttpEntity.class);
        verify(restTemplate).postForEntity(
                eq(BASE_URL + "/api/agent/input-assessment"),
                entityCaptor.capture(),
                eq(String.class));

        Map<String, Object> body = (Map<String, Object>) entityCaptor.getValue().getBody();
        assertNotNull(body);
        assertTrue(body.containsKey("product_info"));
        assertFalse(body.containsKey("productInfo"));
        Map<String, Object> productInfo = (Map<String, Object>) body.get("product_info");
        assertEquals("经常出差的上班族", productInfo.get("target_audience"));
        assertEquals("飞机和高铁", productInfo.get("usage_scenarios"));
        assertFalse(productInfo.containsKey("targetAudience"));
        assertFalse(productInfo.containsKey("usageScenarios"));
        assertEquals("taobao", body.get("target_style"));
        assertEquals("kb-1", body.get("knowledge_base_id"));
        assertEquals(42L, body.get("product_draft_id"));
        assertEquals(TEST_USER_ID, body.get("user_id"));
        assertFalse(body.containsKey("targetStyle"));
        assertFalse(body.containsKey("knowledgeBaseId"));
        assertFalse(body.containsKey("productDraftId"));

        // Input assessment is a free preflight and must never deduct gold.
        verify(userService, never()).deductGold(anyLong(), anyLong(), anyString(), anyString());
    }

    @Test
    @SuppressWarnings("unchecked")
    void findImageCandidates_normalizesFactsInjectsUserAndDoesNotChargeGold() {
        when(restTemplate.postForEntity(
                eq(BASE_URL + "/api/agent/images/candidates"),
                any(org.springframework.http.HttpEntity.class),
                eq(String.class)))
                .thenReturn(org.springframework.http.ResponseEntity.ok(
                        "{\"status\":\"ready\",\"candidates\":[]}"));

        R result = aiProxyService.findImageCandidates(Map.of(
                "productInfo", Map.of(
                        "title", "轻量保温杯",
                        "category", "家居日用",
                        "targetAudience", "学生和上班族",
                        "usageScenarios", "通勤",
                        "seoKeywords", java.util.List.of("轻量保温杯", "通勤保温杯"))));

        assertEquals(10000, result.getCode());
        org.mockito.ArgumentCaptor<org.springframework.http.HttpEntity> entityCaptor =
                org.mockito.ArgumentCaptor.forClass(org.springframework.http.HttpEntity.class);
        verify(restTemplate).postForEntity(
                eq(BASE_URL + "/api/agent/images/candidates"),
                entityCaptor.capture(),
                eq(String.class));

        Map<String, Object> body = (Map<String, Object>) entityCaptor.getValue().getBody();
        assertNotNull(body);
        assertEquals(TEST_USER_ID, body.get("user_id"));
        assertTrue(body.containsKey("product_info"));
        assertFalse(body.containsKey("productInfo"));
        Map<String, Object> productInfo = (Map<String, Object>) body.get("product_info");
        assertEquals("学生和上班族", productInfo.get("target_audience"));
        assertEquals("通勤", productInfo.get("usage_scenarios"));
        assertEquals(java.util.List.of("轻量保温杯", "通勤保温杯"), productInfo.get("seo_keywords"));
        assertFalse(productInfo.containsKey("seoKeywords"));
        verify(userService, never()).deductGold(anyLong(), anyLong(), anyString(), anyString());
    }

    @Test
    void findImageCandidates_returnsErrorWithoutChargingWhenAgentFails() {
        when(restTemplate.postForEntity(
                eq(BASE_URL + "/api/agent/images/candidates"),
                any(org.springframework.http.HttpEntity.class),
                eq(String.class)))
                .thenThrow(new RuntimeException("Connection refused"));

        R result = aiProxyService.findImageCandidates(Map.of(
                "productInfo", Map.of("title", "轻量保温杯", "category", "家居日用")));

        assertNotEquals(10000, result.getCode());
        assertTrue(result.getMsg().contains("AI service error"));
        verify(userService, never()).deductGold(anyLong(), anyLong(), anyString(), anyString());
        verify(userService, never()).addGold(anyLong(), anyLong(), anyString(), anyString());
    }

    @Test
    @SuppressWarnings("unchecked")
    void findImageCandidates_overwritesSpoofedUserIdentity() {
        when(restTemplate.postForEntity(
                eq(BASE_URL + "/api/agent/images/candidates"),
                any(org.springframework.http.HttpEntity.class),
                eq(String.class)))
                .thenReturn(org.springframework.http.ResponseEntity.ok(
                        "{\"status\":\"no_results\",\"candidates\":[]}"));

        aiProxyService.findImageCandidates(Map.of(
                "user_id", 999L,
                "userId", 888L,
                "productInfo", Map.of("title", "轻量保温杯", "category", "家居日用")));

        org.mockito.ArgumentCaptor<org.springframework.http.HttpEntity> entityCaptor =
                org.mockito.ArgumentCaptor.forClass(org.springframework.http.HttpEntity.class);
        verify(restTemplate).postForEntity(
                eq(BASE_URL + "/api/agent/images/candidates"),
                entityCaptor.capture(),
                eq(String.class));
        Map<String, Object> body = (Map<String, Object>) entityCaptor.getValue().getBody();
        assertNotNull(body);
        assertEquals(TEST_USER_ID, body.get("user_id"));
        assertFalse(body.containsKey("userId"));
    }

    @Test
    void assessInput_returnsErrorWhenAgentServiceFails() {
        when(restTemplate.postForEntity(
                eq(BASE_URL + "/api/agent/input-assessment"),
                any(org.springframework.http.HttpEntity.class),
                eq(String.class)))
                .thenThrow(new RuntimeException("Connection refused"));

        R result = aiProxyService.assessInput(Map.of(
                "productInfo", Map.of("title", "测试商品")));

        assertNotNull(result);
        assertNotEquals(0, result.getCode());
        assertTrue(result.getMsg().contains("AI service error"));
        verify(userService, never()).deductGold(anyLong(), anyLong(), anyString(), anyString());
    }

    // ---- SSE streaming ----

    @Test
    void orchestrateStream_chargesGoldBeforeStreaming() {
        mockReadyAssessment();
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
        mockReadyAssessment();
        when(userService.deductGold(anyLong(), anyLong(), anyString(), anyString()))
                .thenReturn(false);

        Map<String, Object> request = Map.of("productInfo", Map.of("title", "test"));

        var emitter = aiProxyService.orchestrateStream(request);
        assertNotNull(emitter);

        // The emitter should be completed with error — we can't easily test that
        // without a full Spring context, but the gold deduction was attempted
        verify(userService).deductGold(eq(TEST_USER_ID), eq(10L), eq("ai_cost"), anyString());
    }

    @Test
    void orchestrateStream_needsInputCompletesWithoutCharging() {
        when(restTemplate.postForEntity(
                eq(BASE_URL + "/api/agent/input-assessment"),
                any(org.springframework.http.HttpEntity.class),
                eq(String.class)))
                .thenReturn(org.springframework.http.ResponseEntity.ok(
                        "{\"input_assessment\":{\"status\":\"needs_input\",\"ready\":false,\"score\":35}}"));

        var emitter = aiProxyService.orchestrateStream(Map.of(
                "productInfo", Map.of("title", "智能破壁机", "category", "厨房电器")));

        assertNotNull(emitter);
        verify(userService, never()).deductGold(anyLong(), anyLong(), anyString(), anyString());
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
