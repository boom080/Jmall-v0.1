package com.jmall.controller;

import com.jmall.common.R;
import com.jmall.dto.AiProxyRequest;
import com.jmall.service.AiProxyService;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.util.Map;

@RestController
@RequestMapping("/api/ai")
public class AiProxyController {

    private final AiProxyService aiProxyService;

    public AiProxyController(AiProxyService aiProxyService) {
        this.aiProxyService = aiProxyService;
    }

    @PostMapping("/orchestrate")
    public R orchestrate(@RequestBody Map<String, Object> request) {
        return aiProxyService.orchestrate(request);
    }

    @PostMapping(value = "/orchestrate/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public SseEmitter orchestrateStream(@RequestBody Map<String, Object> request) {
        return aiProxyService.orchestrateStream(request);
    }

    @PostMapping("/product/copy")
    public R productCopy(@RequestBody Map<String, Object> request) {
        Long productId = request.get("productId") != null ?
                Long.valueOf(request.get("productId").toString()) : null;
        String style = request.get("style") != null ?
                request.get("style").toString() : "taobao";
        return aiProxyService.generateProductCopy(productId, style);
    }

    @PostMapping("/product/review")
    public R productReview(@RequestBody Map<String, Object> request) {
        Long productId = request.get("productId") != null ?
                Long.valueOf(request.get("productId").toString()) : null;
        return aiProxyService.reviewProduct(productId);
    }

    @PostMapping("/product/insights")
    public R productInsights(@RequestBody Map<String, Object> request) {
        Long productId = request.get("productId") != null ?
                Long.valueOf(request.get("productId").toString()) : null;
        return aiProxyService.getProductInsights(productId);
    }

    @GetMapping("/styles")
    public R getStyles() {
        return aiProxyService.getStyles();
    }

    @GetMapping("/knowledge-bases")
    public R getKnowledgeBases() {
        return aiProxyService.getKnowledgeBases();
    }

    @PostMapping("/knowledge-bases")
    public R createKnowledgeBase(@RequestBody Map<String, Object> request) {
        return aiProxyService.createKnowledgeBase(request);
    }

    @PostMapping("/knowledge-bases/upload-txt")
    public R uploadKnowledgeBaseTxt(@RequestBody Map<String, Object> request) {
        String kbId = request.get("kbId") != null ? request.get("kbId").toString() : "";
        String title = request.get("title") != null ? request.get("title").toString() : "粘贴文本";
        String content = request.get("content") != null ?
                request.get("content").toString() : "";
        return aiProxyService.importKnowledgeBaseText(kbId, title, content);
    }

    @GetMapping("/knowledge-bases/{kbId}/documents")
    public R getKnowledgeBaseDocuments(@PathVariable String kbId) {
        return aiProxyService.getKnowledgeBaseDocuments(kbId);
    }

    @DeleteMapping("/knowledge-bases/{kbId}")
    public R deleteKnowledgeBase(@PathVariable String kbId) {
        return aiProxyService.deleteKnowledgeBase(kbId);
    }

    @GetMapping("/admin/cost-stats")
    public R getCostStats() {
        return aiProxyService.getCostStats();
    }

    @GetMapping("/jobs/{jobId}")
    public R getJobStatus(@PathVariable String jobId) {
        return aiProxyService.getJobStatus(jobId);
    }

    @GetMapping("/jobs/active")
    public R getActiveJob() {
        return aiProxyService.getActiveJob();
    }

    @DeleteMapping("/jobs/{jobId}/consume")
    public R consumeJob(@PathVariable String jobId) {
        return aiProxyService.consumeJob(jobId);
    }
}
