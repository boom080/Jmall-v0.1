package com.jmall.controller;

import com.jmall.common.R;
import com.jmall.dto.ProductCreateRequest;
import com.jmall.dto.ProductUpdateRequest;
import com.jmall.service.ProductService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/products")
public class ProductController {

    private final ProductService productService;

    public ProductController(ProductService productService) {
        this.productService = productService;
    }

    @PostMapping
    public R create(@Valid @RequestBody ProductCreateRequest request) {
        return productService.create(request);
    }

    @PutMapping("/{id}")
    public R update(@PathVariable Long id, @Valid @RequestBody ProductUpdateRequest request) {
        return productService.update(id, request);
    }

    @PostMapping("/{id}/publish-check")
    public R publishCheck(@PathVariable Long id) {
        return productService.publishCheck(id);
    }

    @PostMapping("/{id}/publish")
    public R publish(@PathVariable Long id) {
        return productService.publish(id);
    }

    @PostMapping("/{id}/unpublish")
    public R unpublish(@PathVariable Long id) {
        return productService.unpublish(id);
    }

    @GetMapping("/{id}")
    public R getById(@PathVariable Long id,
                     @RequestParam(required = false, defaultValue = "true") Boolean trackView) {
        return productService.getById(id, Boolean.TRUE.equals(trackView));
    }

    @GetMapping
    public R list(@RequestParam(required = false) String category,
                  @RequestParam(required = false) String style,
                  @RequestParam(required = false) String status,
                  @RequestParam(required = false) String keyword,
                  @RequestParam(required = false) Long storeId,
                  @RequestParam(required = false, defaultValue = "1") Integer page,
                  @RequestParam(required = false, defaultValue = "20") Integer size) {
        return productService.list(category, style, status, keyword, storeId, page, size);
    }

    @DeleteMapping("/{id}")
    public R delete(@PathVariable Long id) {
        return productService.delete(id);
    }

    @GetMapping("/mine")
    public R getMyProducts(@RequestParam(required = false, defaultValue = "1") Integer page,
                           @RequestParam(required = false, defaultValue = "20") Integer size) {
        return productService.getMyProducts(page, size);
    }
}
