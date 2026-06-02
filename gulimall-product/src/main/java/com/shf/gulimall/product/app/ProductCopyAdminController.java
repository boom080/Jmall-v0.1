package com.shf.gulimall.product.app;

import com.shf.common.utils.R;
import com.shf.gulimall.product.app.dto.ProductCopyGenerateRequest;
import com.shf.gulimall.product.app.dto.ProductCopyGenerateResponse;
import com.shf.gulimall.product.app.service.ProductAiApplicationService;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import javax.validation.Valid;

@RestController
@RequestMapping("product/ai/product-copy")
public class ProductCopyAdminController {

    private final ProductAiApplicationService productAiApplicationService;

    public ProductCopyAdminController(ProductAiApplicationService productAiApplicationService) {
        this.productAiApplicationService = productAiApplicationService;
    }

    @PostMapping({"", "/generate"})
    public R generateProductCopy(@Valid @RequestBody ProductCopyGenerateRequest request) {
        ProductCopyGenerateResponse response = productAiApplicationService.generateProductCopy(request);
        return R.ok(response.getMessage()).setData(response);
    }
}





