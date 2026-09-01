package com.jmall.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.jmall.common.R;
import com.jmall.dto.PublishCheckResult;
import com.jmall.entity.Product;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.anyMap;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

class ProductPublishServiceTest {

    private AiProxyService aiProxyService;
    private ProductPublishService publishService;

    @BeforeEach
    void setUp() {
        aiProxyService = mock(AiProxyService.class);
        publishService = new ProductPublishService(aiProxyService, new ObjectMapper());
    }

    @Test
    void validUploadedImageDraftIsPublishable() {
        mockAssessment(true, List.of());
        Product product = validProduct();
        product.setImages("[\"/uploads/cup.jpg\"]");

        PublishCheckResult result = publishService.check(product);

        assertTrue(result.publishable());
        assertTrue(result.publishBlockers().isEmpty());
    }

    @Test
    void missingCoreFieldsAndImageReturnStructuredBlockers() {
        mockAssessment(false, List.of("请补充商品事实"));
        Product product = new Product();
        product.setTitle("");
        product.setCategory("");
        product.setPrice(0L);
        product.setDescription("");

        PublishCheckResult result = publishService.check(product);

        assertFalse(result.publishable());
        assertTrue(hasCode(result, "title_required"));
        assertTrue(hasCode(result, "category_required"));
        assertTrue(hasCode(result, "price_invalid"));
        assertTrue(hasCode(result, "description_required"));
        assertTrue(hasCode(result, "image_required"));
        assertTrue(hasCode(result, "input_not_ready"));
    }

    @Test
    void externalSearchImageRequiresMatchingExplicitConfirmation() {
        mockAssessment(true, List.of());
        Product product = validProduct();
        product.setImages("[\"https://images.example.com/cup.jpg\"]");
        product.setAiDraftMeta("{\"selected_image_source\":{\"user_confirmed\":true," +
                "\"original_url\":\"https://images.example.com/other.jpg\"," +
                "\"source_page_url\":\"https://publisher.example.com/cup\"}}");

        PublishCheckResult result = publishService.check(product);

        assertFalse(result.publishable());
        assertTrue(hasCode(result, "search_image_unconfirmed"));
    }

    @Test
    void matchingConfirmedSearchImageCanPass() {
        mockAssessment(true, List.of());
        Product product = validProduct();
        product.setImages("[\"https://images.example.com/cup.jpg\"]");
        product.setAiDraftMeta("{\"selected_image_source\":{\"user_confirmed\":true," +
                "\"original_url\":\"https://images.example.com/cup.jpg\"," +
                "\"source_page_url\":\"https://publisher.example.com/cup\"}}");

        assertTrue(publishService.check(product).publishable());
    }

    @Test
    void pendingConfirmationAndRejectedComplianceBlockPublishing() {
        mockAssessment(true, List.of());
        Product product = validProduct();
        product.setImages("[\"/uploads/cup.jpg\"]");
        product.setAiDraftMeta("{\"pending_confirmations\":[\"保温时长待确认\"]}");
        product.setComplianceResult("{\"status\":\"rejected\"}");

        PublishCheckResult result = publishService.check(product);

        assertFalse(result.publishable());
        assertTrue(hasCode(result, "pending_confirmations"));
        assertTrue(hasCode(result, "compliance_rejected"));
    }

    @Test
    void invalidOrPrivateImageUrlIsRejected() {
        mockAssessment(true, List.of());
        Product product = validProduct();
        product.setImages("[\"https://127.0.0.1/private.jpg\"]");

        PublishCheckResult result = publishService.check(product);

        assertFalse(result.publishable());
        assertTrue(hasCode(result, "image_url_invalid"));
    }

    private void mockAssessment(boolean ready, List<String> questions) {
        when(aiProxyService.assessInput(anyMap())).thenReturn(R.ok(Map.of(
                "input_assessment", Map.of(
                        "ready", ready,
                        "questions", questions))));
    }

    @Test
    void switchingPlatformCannotPublishOldPlatformDraft() {
        mockAssessment(true, List.of());
        Product product = validProduct();
        product.setImages("[\"/uploads/cup.jpg\"]");
        product.setStyle("jd");
        product.setAiDraftMeta("{\"platform_style\":\"taobao\",\"platform_skill_id\":\"taobao_listing_v1\",\"platform_skill_version\":\"1.0.0\"}");
        assertTrue(hasCode(publishService.check(product), "platform_mismatch"));
        product.setStyle("taobao");
        assertTrue(publishService.check(product).publishable());
    }

    private Product validProduct() {
        Product product = new Product();
        product.setTitle("轻量保温杯");
        product.setCategory("家居日用");
        product.setPrice(9900L);
        product.setDescription("食品级 304 不锈钢，500ml，适合学生和上班族通勤使用。");
        product.setAiDraftMeta("{\"input_snapshot\":{\"specifications\":\"304不锈钢；500ml\"," +
                "\"targetAudience\":\"学生和上班族\"}}");
        return product;
    }

    private boolean hasCode(PublishCheckResult result, String code) {
        return result.publishBlockers().stream().anyMatch(blocker -> code.equals(blocker.code()));
    }
}
