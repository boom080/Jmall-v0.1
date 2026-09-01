package com.jmall.service;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.jmall.common.BizCodeEnum;
import com.jmall.common.R;
import com.jmall.dto.PublishBlocker;
import com.jmall.dto.PublishCheckResult;
import com.jmall.entity.Product;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.net.URI;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

@Service
public class ProductPublishService {

    private final AiProxyService aiProxyService;
    private final ObjectMapper objectMapper;

    public ProductPublishService(AiProxyService aiProxyService, ObjectMapper objectMapper) {
        this.aiProxyService = aiProxyService;
        this.objectMapper = objectMapper;
    }

    public PublishCheckResult check(Product product) {
        List<PublishBlocker> blockers = new ArrayList<>();
        requireText(blockers, product.getTitle(), "title_required", "title", "请填写商品名称");
        requireText(blockers, product.getCategory(), "category_required", "category", "请选择商品品类");
        if (product.getPrice() == null || product.getPrice() <= 0) {
            blockers.add(new PublishBlocker("price_invalid", "price", "商品价格必须大于 0"));
        }
        requireText(blockers, product.getDescription(), "description_required", "description", "请填写商品详情");

        Map<String, Object> metadata = parseObject(product.getAiDraftMeta(), blockers);
        validatePlatform(product, metadata, blockers);
        validateImages(product.getImages(), metadata, blockers);
        validatePendingConfirmations(metadata, blockers);
        validateCompliance(product.getComplianceResult(), blockers);
        validateInputAssessment(product, metadata, blockers);

        return new PublishCheckResult(blockers.isEmpty(), List.copyOf(blockers));
    }

    private void validateInputAssessment(Product product, Map<String, Object> metadata,
                                         List<PublishBlocker> blockers) {
        Map<String, Object> productInfo = new LinkedHashMap<>();
        Object snapshot = metadata.get("input_snapshot");
        if (snapshot instanceof Map<?, ?> snapshotMap) {
            snapshotMap.forEach((key, value) -> productInfo.put(String.valueOf(key), value));
        }
        productInfo.put("title", product.getTitle() == null ? "" : product.getTitle());
        productInfo.put("category", product.getCategory() == null ? "" : product.getCategory());
        productInfo.put("description", product.getDescription() == null ? "" : product.getDescription());

        R assessmentResponse = aiProxyService.assessInput(Map.of(
                "productInfo", productInfo,
                "targetStyle", StringUtils.hasText(product.getStyle()) ? product.getStyle() : "taobao"));
        if (assessmentResponse.getCode() != BizCodeEnum.SUCCESS.getCode()
                || !(assessmentResponse.getData() instanceof Map<?, ?> root)) {
            blockers.add(new PublishBlocker(
                    "input_assessment_unavailable", "input", "商品信息体检暂时不可用，请稍后重试"));
            return;
        }
        Object assessmentValue = root.get("input_assessment");
        if (!(assessmentValue instanceof Map<?, ?> assessment)
                || !Boolean.TRUE.equals(assessment.get("ready"))) {
            blockers.add(new PublishBlocker(
                    "input_not_ready", "input", firstAssessmentQuestion(assessmentValue)));
        }
    }

    private String firstAssessmentQuestion(Object assessmentValue) {
        if (assessmentValue instanceof Map<?, ?> assessment) {
            Object questionsValue = assessment.get("questions");
            if (questionsValue instanceof List<?> questions && !questions.isEmpty()) {
                return String.valueOf(questions.get(0));
            }
        }
        return "商品信息尚不完整，请补充真实特点和目标人群";
    }

    private void validatePlatform(Product product, Map<String, Object> metadata,
                                  List<PublishBlocker> blockers) {
        Object generatedStyle = metadata.getOrDefault("platform_style", metadata.get("target_style"));
        // v0.1/manual products have no provenance. Do not invent a Skill or
        // block their normal edits; enforce consistency when one is recorded.
        if (hasTextValue(generatedStyle)
                && !String.valueOf(generatedStyle).equals(product.getStyle())) {
            blockers.add(new PublishBlocker("platform_mismatch", "style",
                    "当前文案属于其他平台，请为所选平台重新生成或切回原平台"));
        }
    }

    private void validateImages(String rawImages, Map<String, Object> metadata,
                                List<PublishBlocker> blockers) {
        List<String> images = parseImages(rawImages);
        if (images.isEmpty()) {
            blockers.add(new PublishBlocker("image_required", "images", "请至少上传或确认使用一张商品图片"));
            return;
        }
        boolean invalidUrl = images.stream().anyMatch(value -> !isPublishableImageUrl(value));
        if (invalidUrl) {
            blockers.add(new PublishBlocker("image_url_invalid", "images", "商品图片包含不安全或无效的链接"));
            return;
        }
        boolean hasUploadedImage = images.stream().anyMatch(ProductPublishService::isUploadedImage);
        if (hasUploadedImage) return;

        Object selectedValue = metadata.get("selected_image_source");
        if (!(selectedValue instanceof Map<?, ?> selected)
                || !Boolean.TRUE.equals(selected.get("user_confirmed"))
                || !images.contains(String.valueOf(selected.get("original_url")))
                || !hasTextValue(selected.get("source_page_url"))) {
            blockers.add(new PublishBlocker(
                    "search_image_unconfirmed", "images", "搜索图片必须先确认来源与使用风险"));
        }
    }

    private List<String> parseImages(String rawImages) {
        if (!StringUtils.hasText(rawImages)) return List.of();
        try {
            Object parsed = objectMapper.readValue(rawImages, Object.class);
            if (parsed instanceof List<?> values) {
                return values.stream().map(String::valueOf).filter(StringUtils::hasText).toList();
            }
        } catch (Exception ignored) {
            // Support the v0.1 comma-separated representation during migration.
        }
        return List.of(rawImages.split(",")).stream().map(String::trim)
                .filter(StringUtils::hasText).toList();
    }

    private static boolean isUploadedImage(String value) {
        return value.startsWith("/uploads/");
    }

    private static boolean isPublishableImageUrl(String value) {
        if (isUploadedImage(value)) return true;
        try {
            if (value.length() > 2048 || value.chars().anyMatch(Character::isWhitespace)) return false;
            URI uri = URI.create(value);
            String host = uri.getHost();
            if (!"https".equalsIgnoreCase(uri.getScheme()) || !StringUtils.hasText(host)
                    || uri.getUserInfo() != null) return false;
            String normalizedHost = host.toLowerCase(Locale.ROOT);
            if (normalizedHost.equals("localhost") || normalizedHost.endsWith(".localhost")
                    || normalizedHost.endsWith(".local") || normalizedHost.endsWith(".internal")) return false;
            return !normalizedHost.matches("^(127\\.|10\\.|192\\.168\\.|169\\.254\\.|0\\.|224\\.|255\\.).*")
                    && !normalizedHost.matches("^172\\.(1[6-9]|2[0-9]|3[01])\\..*")
                    && !normalizedHost.equals("::1");
        } catch (Exception ignored) {
            return false;
        }
    }

    private void validatePendingConfirmations(Map<String, Object> metadata,
                                              List<PublishBlocker> blockers) {
        Object pending = metadata.get("pending_confirmations");
        if (pending instanceof List<?> values && !values.isEmpty()) {
            blockers.add(new PublishBlocker(
                    "pending_confirmations", "confirmations", "仍有内容需要确认，请补充事实后重新运行 AI 检查"));
        }
    }

    private void validateCompliance(String rawCompliance, List<PublishBlocker> blockers) {
        if (!StringUtils.hasText(rawCompliance)) return;
        try {
            Map<String, Object> compliance = objectMapper.readValue(
                    rawCompliance, new TypeReference<Map<String, Object>>() {});
            Object status = compliance.get("status");
            if ("rejected".equalsIgnoreCase(String.valueOf(status))) {
                blockers.add(new PublishBlocker("compliance_rejected", "compliance", "合规审查未通过"));
            }
        } catch (Exception ignored) {
            blockers.add(new PublishBlocker("compliance_invalid", "compliance", "合规审查结果格式无效，请重新检查"));
        }
    }

    private Map<String, Object> parseObject(String raw, List<PublishBlocker> blockers) {
        if (!StringUtils.hasText(raw)) return new LinkedHashMap<>();
        try {
            return objectMapper.readValue(raw, new TypeReference<Map<String, Object>>() {});
        } catch (Exception ignored) {
            blockers.add(new PublishBlocker("draft_meta_invalid", "draft", "草稿元数据格式无效，请重新保存"));
            return new LinkedHashMap<>();
        }
    }

    private static void requireText(List<PublishBlocker> blockers, String value,
                                    String code, String field, String message) {
        if (!StringUtils.hasText(value)) blockers.add(new PublishBlocker(code, field, message));
    }

    private static boolean hasTextValue(Object value) {
        return value instanceof String text && StringUtils.hasText(text);
    }
}
