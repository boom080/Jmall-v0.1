package com.jmall.service;

import com.jmall.common.R;
import com.jmall.common.UserContext;
import com.jmall.dto.AiProxyRequest;
import org.springframework.beans.factory.annotation.Value;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.http.*;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

@Service
public class AiProxyService {

    private static final Logger log = LoggerFactory.getLogger(AiProxyService.class);

    private final RestTemplate restTemplate;
    private final UserService userService;

    @Value("${jmall.ai.base-url}")
    private String aiBaseUrl;

    // AI operation costs in gold (1 gold = 1 yuan)
    private static final long COST_ORCHESTRATE = 10L;
    private static final long COST_PRODUCT_COPY = 5L;
    private static final long COST_PRODUCT_REVIEW = 5L;
    private static final long COST_PRODUCT_INSIGHTS = 5L;

    public AiProxyService(UserService userService) {
        // Configure RestTemplate with timeouts (connect: 10s, read: 120s)
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(10_000);  // 10 seconds
        factory.setReadTimeout(120_000);    // 120 seconds
        this.restTemplate = new RestTemplate(factory);
        this.userService = userService;
    }

    // Thread pool for SSE streaming
    private final ExecutorService sseExecutor = Executors.newCachedThreadPool();

    /**
     * Convert camelCase field names to snake_case for Python agent compatibility.
     * The frontend sends camelCase (productInfo), but the Python agent expects snake_case (product_info).
     */
    @SuppressWarnings("unchecked")
    private Map<String, Object> normalizeForAgent(Map<String, Object> request) {
        Map<String, Object> normalized = new HashMap<>(request);

        // Convert productInfo -> product_info
        if (normalized.containsKey("productInfo") && !normalized.containsKey("product_info")) {
            normalized.put("product_info", normalized.remove("productInfo"));
        }
        // Convert targetStyle -> target_style
        if (normalized.containsKey("targetStyle") && !normalized.containsKey("target_style")) {
            normalized.put("target_style", normalized.remove("targetStyle"));
        }
        // Convert knowledgeBaseId -> knowledge_base_id
        if (normalized.containsKey("knowledgeBaseId") && !normalized.containsKey("knowledge_base_id")) {
            normalized.put("knowledge_base_id", normalized.remove("knowledgeBaseId"));
        }
        // Convert userRequest -> user_request
        if (normalized.containsKey("userRequest") && !normalized.containsKey("user_request")) {
            normalized.put("user_request", normalized.remove("userRequest"));
        }
        if (normalized.containsKey("productDraftId") && !normalized.containsKey("product_draft_id")) {
            normalized.put("product_draft_id", normalized.remove("productDraftId"));
        }

        // Also normalize nested productInfo inside product_info if it was already snake_case
        if (normalized.containsKey("product_info") && normalized.get("product_info") instanceof Map) {
            Map<String, Object> pi = new HashMap<>((Map<String, Object>) normalized.get("product_info"));
            if (pi.containsKey("productInfo")) {
                // Already in the right place, but sub-fields need conversion - they should be fine
                // since the value is already a Map with title/category/description/price
            }
            normalized.put("product_info", pi);
        }

        return normalized;
    }

    public R orchestrate(Map<String, Object> request) {
        Map<String, Object> normalized = normalizeForAgent(request);
        Long userId = UserContext.getUserId();
        if (userId != null) {
            normalized.put("user_id", userId);
        }
        return forwardAndCharge("/api/agent/orchestrate", normalized, COST_ORCHESTRATE);
    }

    public SseEmitter orchestrateStream(Map<String, Object> request) {
        SseEmitter emitter = new SseEmitter(300_000L); // 5 minute timeout

        Long userId = UserContext.getUserId();

        // Normalize field names for Python agent (camelCase -> snake_case)
        final Map<String, Object> normalizedRequest = normalizeForAgent(request);
        if (userId != null) {
            normalizedRequest.put("user_id", userId);
        }

        // Charge gold
        if (userId != null && COST_ORCHESTRATE > 0) {
            boolean deducted = userService.deductGold(userId, COST_ORCHESTRATE, "ai_cost",
                    "AI service usage (stream)");
            if (!deducted) {
                emitter.completeWithError(
                        new RuntimeException("insufficient gold for AI service (cost: " + COST_ORCHESTRATE + ")"));
                return emitter;
            }
        }

        final long finalUserId = userId != null ? userId : 0L;

        sseExecutor.execute(() -> {
            long startedAt = System.currentTimeMillis();
            boolean[] firstEventLogged = {false};
            boolean[] jobCreated = {false};
            try {
                String url = aiBaseUrl + "/api/agent/orchestrate/stream";
                HttpHeaders headers = new HttpHeaders();
                headers.setContentType(MediaType.APPLICATION_JSON);
                HttpEntity<Object> entity = new HttpEntity<>(normalizedRequest, headers);

                // Use RestTemplate with timeouts for SSE stream (connect: 10s, read: 300s for long streaming)
                SimpleClientHttpRequestFactory sseFactory = new SimpleClientHttpRequestFactory();
                sseFactory.setConnectTimeout(10_000);
                sseFactory.setReadTimeout(300_000);
                RestTemplate sseRestTemplate = new RestTemplate(sseFactory);
                log.info("AI SSE proxy start userId={} draftId={} url={}", finalUserId,
                        normalizedRequest.get("product_draft_id"), url);
                // Execute with response extraction for SSE streaming
                sseRestTemplate.execute(url, HttpMethod.POST,
                        req -> {
                            req.getHeaders().setContentType(MediaType.APPLICATION_JSON);
                            req.getBody().write(new ObjectMapper().writeValueAsBytes(normalizedRequest));
                        },
                        res -> {
                            try (BufferedReader reader = new BufferedReader(
                                    new InputStreamReader(res.getBody(), StandardCharsets.UTF_8))) {
                                String line;
                                StringBuilder eventData = new StringBuilder();
                                String eventName = "message";

                                while ((line = reader.readLine()) != null) {
                                    if (line.startsWith("event:")) {
                                        eventName = line.substring(6).trim();
                                    } else if (line.startsWith("data:")) {
                                        String chunk = line.substring(5);
                                        eventData.append(chunk.startsWith(" ") ? chunk.substring(1) : chunk);
                                    } else if (line.isEmpty() && eventData.length() > 0) {
                                        // Complete event — forward it
                                        // Mark durability before forwarding. If the browser
                                        // disconnects during this send, the Python job already
                                        // exists and must not be refunded or cancelled.
                                        if ("job_created".equals(eventName)) {
                                            jobCreated[0] = true;
                                        }
                                        try {
                                            Map<String, Object> parsed = new ObjectMapper()
                                                    .readValue(eventData.toString(), Map.class);
                                            emitter.send(SseEmitter.event()
                                                    .name(eventName)
                                                    .data(parsed));
                                        } catch (Exception e) {
                                            emitter.send(SseEmitter.event()
                                                    .name(eventName)
                                                    .data(eventData.toString()));
                                        }
                                        if (!firstEventLogged[0]) {
                                            log.info("AI SSE proxy first event userId={} event={} elapsedMs={}",
                                                    finalUserId, eventName, System.currentTimeMillis() - startedAt);
                                            firstEventLogged[0] = true;
                                        }
                                        eventData.setLength(0);
                                        eventName = "message";
                                    }
                                    // Skip comments (lines starting with ":")
                                }
                            }
                            return null;
                        });

                emitter.complete();
                log.info("AI SSE proxy complete userId={} elapsedMs={}", finalUserId,
                        System.currentTimeMillis() - startedAt);
            } catch (Exception e) {
                if (jobCreated[0]) {
                    // The durable Python job keeps running after the browser closes
                    // this proxy stream. The user can recover it via /jobs/active.
                    log.warn("AI SSE client detached after durable job creation userId={} elapsedMs={} reason={}",
                            finalUserId, System.currentTimeMillis() - startedAt, e.getMessage());
                    emitter.complete();
                    return;
                }
                log.error("AI SSE proxy failed before job creation userId={} elapsedMs={}", finalUserId,
                        System.currentTimeMillis() - startedAt, e);
                // Refund on failure
                if (finalUserId > 0 && COST_ORCHESTRATE > 0) {
                    try {
                        userService.addGold(finalUserId, COST_ORCHESTRATE, "refund",
                                "Refund for failed AI stream service");
                    } catch (Exception ignored) {}
                }
                try {
                    emitter.send(SseEmitter.event()
                            .name("error")
                            .data(Map.of("error", "AI service error: " + e.getMessage())));
                } catch (Exception ignored) {}
                emitter.completeWithError(e);
            }
        });

        return emitter;
    }

    public R generateProductCopy(Long productId, String style) {
        Map<String, Object> payload = new HashMap<>();
        payload.put("product_id", productId);
        payload.put("style", style);
        return forwardAndCharge("/api/agent/product/copy", payload, COST_PRODUCT_COPY);
    }

    public R reviewProduct(Long productId) {
        Map<String, Object> payload = new HashMap<>();
        payload.put("product_id", productId);
        return forwardAndCharge("/api/agent/product/review", payload, COST_PRODUCT_REVIEW);
    }

    public R getProductInsights(Long productId) {
        Map<String, Object> payload = new HashMap<>();
        payload.put("product_id", productId);
        return forwardAndCharge("/api/agent/product/insights", payload, COST_PRODUCT_INSIGHTS);
    }

    public R getStyles() {
        return forwardGet("/api/styles");
    }

    public R getKnowledgeBases() {
        return forwardGet("/api/merchant/knowledge-bases");
    }

    public R createKnowledgeBase(Map<String, Object> request) {
        return forwardPost("/api/merchant/knowledge-bases", request);
    }

    public R importKnowledgeBaseText(String kbId, String title, String content) {
        Map<String, Object> payload = new HashMap<>();
        payload.put("title", title);
        payload.put("content", content);
        return forwardPost("/api/merchant/knowledge-bases/" + kbId + "/documents/text", payload);
    }

    public R getKnowledgeBaseDocuments(String kbId) {
        return forwardGet("/api/merchant/knowledge-bases/" + kbId + "/documents");
    }

    public R deleteKnowledgeBase(String kbId) {
        return forwardDelete("/api/merchant/knowledge-bases/" + kbId);
    }

    public R getCostStats() {
        return forwardGet("/api/admin/cost-stats");
    }

    public R getJobStatus(String jobId) {
        Long userId = UserContext.getUserId();
        String suffix = userId == null ? "" : "?user_id=" + userId;
        return forwardGet("/api/agent/jobs/" + jobId + suffix);
    }

    public R getActiveJob() {
        Long userId = UserContext.getUserId();
        if (userId == null) {
            return R.error(40100, "not logged in");
        }
        return forwardGet("/api/agent/jobs/active/" + userId);
    }

    public R consumeJob(String jobId) {
        Long userId = UserContext.getUserId();
        if (userId == null) {
            return R.error(40100, "not logged in");
        }
        return forwardDelete("/api/agent/jobs/" + jobId + "/consume?user_id=" + userId);
    }

    private R forwardGet(String path) {
        try {
            String url = aiBaseUrl + path;
            HttpHeaders headers = new HttpHeaders();
            HttpEntity<Void> entity = new HttpEntity<>(headers);
            ResponseEntity<String> response = restTemplate.exchange(url, HttpMethod.GET, entity, String.class);
            return parseForwardResponse(response);
        } catch (Exception e) {
            return R.error(50001, "AI service error: " + e.getMessage());
        }
    }

    private R forwardPost(String path, Object body) {
        try {
            String url = aiBaseUrl + path;
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            HttpEntity<Object> entity = new HttpEntity<>(body, headers);
            ResponseEntity<String> response = restTemplate.postForEntity(url, entity, String.class);
            return parseForwardResponse(response);
        } catch (Exception e) {
            return R.error(50001, "AI service error: " + e.getMessage());
        }
    }

    private R forwardDelete(String path) {
        try {
            String url = aiBaseUrl + path;
            HttpHeaders headers = new HttpHeaders();
            HttpEntity<Void> entity = new HttpEntity<>(headers);
            ResponseEntity<String> response = restTemplate.exchange(url, HttpMethod.DELETE, entity, String.class);
            return parseForwardResponse(response);
        } catch (Exception e) {
            return R.error(50001, "AI service error: " + e.getMessage());
        }
    }

    @SuppressWarnings("unchecked")
    private R parseForwardResponse(ResponseEntity<String> response) {
        try {
            ObjectMapper mapper = new ObjectMapper();
            Object parsed = mapper.readValue(response.getBody(), Object.class);
            return R.ok(parsed);
        } catch (Exception e) {
            // Fallback: return as raw string if parsing fails
            return R.ok(response.getBody());
        }
    }

    private R forwardAndCharge(String path, Object body, long cost) {
        Long userId = UserContext.getUserId();

        // Check and deduct gold
        if (userId != null && cost > 0) {
            boolean deducted = userService.deductGold(userId, cost, "ai_cost",
                    "AI service usage");
            if (!deducted) {
                return R.error(10020, "insufficient gold for AI service (cost: " + cost + ")");
            }
        }

        try {
            String url = aiBaseUrl + path;
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            HttpEntity<Object> entity = new HttpEntity<>(body, headers);

            ResponseEntity<String> response = restTemplate.postForEntity(url, entity, String.class);
            return R.ok("AI service response", response.getBody());
        } catch (Exception e) {
            // Refund gold on failure
            if (userId != null && cost > 0) {
                userService.addGold(userId, cost, "refund",
                        "Refund for failed AI service");
            }
            return R.error(50001, "AI service error: " + e.getMessage());
        }
    }
}
