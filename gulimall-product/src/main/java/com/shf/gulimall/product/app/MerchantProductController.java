package com.shf.gulimall.product.app;

import com.shf.common.utils.R;
import com.shf.gulimall.product.app.dto.MerchantImageUploadResponse;
import com.shf.gulimall.product.app.dto.MerchantProductResponse;
import com.shf.gulimall.product.app.dto.MerchantProductUpdateRequest;
import com.shf.gulimall.product.app.service.MerchantProductApplicationService;
import com.shf.gulimall.product.app.service.MerchantProductImageStorageService;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequestMapping("product/merchant/products")
public class MerchantProductController {

    private final MerchantProductApplicationService merchantProductApplicationService;
    private final MerchantProductImageStorageService merchantProductImageStorageService;

    public MerchantProductController(MerchantProductApplicationService merchantProductApplicationService,
                                    MerchantProductImageStorageService merchantProductImageStorageService) {
        this.merchantProductApplicationService = merchantProductApplicationService;
        this.merchantProductImageStorageService = merchantProductImageStorageService;
    }

    @GetMapping
    public R listProducts() {
        return R.ok().setData(merchantProductApplicationService.listProducts());
    }

    @GetMapping("/{skuId}")
    public R getProduct(@PathVariable("skuId") Long skuId) {
        MerchantProductResponse response = merchantProductApplicationService.getProduct(skuId);
        if (response == null) {
            return R.error(404, "商品不存在");
        }
        return R.ok().setData(response);
    }

    @PostMapping
    public R createProduct(@RequestBody MerchantProductUpdateRequest request) {
        try {
            return R.ok().setData(merchantProductApplicationService.createProduct(request));
        } catch (IllegalArgumentException ex) {
            return R.error(400, ex.getMessage());
        }
    }

    @PutMapping("/{skuId}")
    public R updateProduct(@PathVariable("skuId") Long skuId, @RequestBody MerchantProductUpdateRequest request) {
        try {
            return R.ok().setData(merchantProductApplicationService.updateProduct(skuId, request));
        } catch (IllegalArgumentException ex) {
            return R.error(400, ex.getMessage());
        }
    }

    @PostMapping(value = "/upload-image", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public R uploadProductImage(@RequestParam("file") MultipartFile file) {
        try {
            MerchantImageUploadResponse response = merchantProductImageStorageService.uploadProductImage(file);
            return R.ok().setData(response);
        } catch (IllegalArgumentException ex) {
            return R.error(400, ex.getMessage());
        } catch (IllegalStateException ex) {
            return R.error(503, ex.getMessage());
        }
    }
}





