package com.jmall.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.net.URI;
import java.util.*;

/**
 * Image generation via Qwen (阿里百炼 DashScope).
 * Uses text-to-image API to generate product main images.
 * Falls back to placeholder on failure.
 */
@Service
public class ImageGenerationService {

    private static final Logger log = LoggerFactory.getLogger(ImageGenerationService.class);
    private static final String PLACEHOLDER = "https://placehold.co/600x400/e8e8e8/666?text=商品图片";

    private final RestTemplate restTemplate;
    private final ObjectMapper objectMapper;
    private final String apiKey;

    public ImageGenerationService(@Value("${JMALL_QWEN_API_KEY:}") String apiKey) {
        this.restTemplate = new RestTemplate();
        this.objectMapper = new ObjectMapper();
        this.apiKey = apiKey;
    }

    /**
     * Generate a product image based on name and category.
     * Returns a placeholder URL if generation fails or API key is missing.
     */
    public String generate(String productName, String category) {
        if (apiKey == null || apiKey.isBlank()) {
            log.warn("Qwen API key not configured, using placeholder image");
            return placeholderFor(category);
        }

        try {
            String prompt = buildPrompt(productName, category);

            Map<String, Object> input = new HashMap<>();
            input.put("prompt", prompt);
            input.put("negative_prompt", "blurry, low quality, text, watermark, logo, distorted");
            input.put("size", "1024*1024");
            input.put("n", 1);

            Map<String, Object> body = new HashMap<>();
            body.put("model", "qwen-image-max");
            body.put("input", input);

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            headers.set("Authorization", "Bearer " + apiKey);

            HttpEntity<Map<String, Object>> entity = new HttpEntity<>(body, headers);
            URI uri = URI.create("https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation");

            ResponseEntity<String> resp = restTemplate.exchange(uri, HttpMethod.POST, entity, String.class);

            if (resp.getStatusCode().is2xxSuccessful() && resp.getBody() != null) {
                JsonNode root = objectMapper.readTree(resp.getBody());
                JsonNode output = root.path("output");
                JsonNode results = output.path("results");
                if (results.isArray() && results.size() > 0) {
                    String url = results.get(0).path("url").asText();
                    if (url != null && !url.isBlank()) {
                        log.info("Image generated successfully for: {}", productName);
                        return url;
                    }
                }
            }

            log.warn("Image generation returned unexpected response: {}", resp.getStatusCode());
        } catch (Exception e) {
            log.warn("Image generation failed for '{}': {}", productName, e.getMessage());
        }

        return placeholderFor(category);
    }

    private String buildPrompt(String name, String category) {
        StringBuilder sb = new StringBuilder();
        sb.append("Professional e-commerce product photo of ");
        sb.append(name).append(", ");
        sb.append(category).append(" category, ");
        sb.append("clean white background, studio lighting, high resolution, ");
        sb.append("commercial photography style, detailed texture, 8k quality, ");
        sb.append("no text overlay, no watermarks");
        return sb.toString();
    }

    private String placeholderFor(String category) {
        // Return a themed placeholder based on category
        String color = switch (category) {
            case "茶叶", "食品饮料" -> "8BC34A";
            case "手机数码" -> "2196F3";
            case "厨房电器", "数码家电" -> "FF9800";
            case "服饰鞋包" -> "E91E63";
            default -> "9E9E9E";
        };
        return "https://placehold.co/600x400/" + color + "/white?text=" + category;
    }
}
