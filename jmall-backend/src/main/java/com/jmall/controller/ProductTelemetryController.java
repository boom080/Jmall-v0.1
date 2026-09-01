package com.jmall.controller;

import com.jmall.common.BizCodeEnum;
import com.jmall.common.R;
import com.jmall.common.UserContext;
import com.jmall.dto.EditorEventRequest;
import com.jmall.service.ProductMetrics;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
@RequestMapping("/api/telemetry")
public class ProductTelemetryController {

    private final ProductMetrics productMetrics;

    public ProductTelemetryController(ProductMetrics productMetrics) {
        this.productMetrics = productMetrics;
    }

    @PostMapping("/editor-events")
    public R recordEditorEvent(@Valid @RequestBody EditorEventRequest request) {
        if (UserContext.getUserId() == null) {
            return R.error(BizCodeEnum.AUTH_ERROR);
        }
        boolean recorded = productMetrics.recordEditorEvent(request.getSessionId(), request.getStage());
        return R.ok(Map.of("recorded", recorded));
    }
}
