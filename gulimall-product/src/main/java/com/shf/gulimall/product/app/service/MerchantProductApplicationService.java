package com.shf.gulimall.product.app.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.shf.gulimall.product.app.dto.MerchantProductListResponse;
import com.shf.gulimall.product.app.dto.MerchantProductResponse;
import com.shf.gulimall.product.app.dto.MerchantProductUpdateRequest;
import com.shf.gulimall.product.entity.CategoryEntity;
import com.shf.gulimall.product.entity.SkuInfoEntity;
import com.shf.gulimall.product.entity.SpuInfoEntity;
import com.shf.gulimall.product.service.CategoryService;
import com.shf.gulimall.product.service.SkuInfoService;
import com.shf.gulimall.product.service.SpuInfoService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Date;
import java.util.List;

@Service
public class MerchantProductApplicationService {

    private static final Logger log = LoggerFactory.getLogger(MerchantProductApplicationService.class);

    private static final String STATUS_DRAFT = "draft";
    private static final String STATUS_READY = "ready";

    private final SkuInfoService skuInfoService;
    private final SpuInfoService spuInfoService;
    private final CategoryService categoryService;

    public MerchantProductApplicationService(SkuInfoService skuInfoService,
                                             SpuInfoService spuInfoService,
                                             CategoryService categoryService) {
        this.skuInfoService = skuInfoService;
        this.spuInfoService = spuInfoService;
        this.categoryService = categoryService;
    }

    public MerchantProductListResponse listProducts() {
        List<SkuInfoEntity> skus = skuInfoService.list(new QueryWrapper<SkuInfoEntity>()
                .orderByDesc("sku_id")
                .last("limit 100"));
        MerchantProductListResponse response = new MerchantProductListResponse();
        List<MerchantProductResponse> items = new ArrayList<MerchantProductResponse>();
        for (SkuInfoEntity sku : skus) {
            items.add(toResponse(sku));
        }
        response.setItems(items);
        return response;
    }

    public MerchantProductResponse getProduct(Long skuId) {
        validateSkuId(skuId);
        SkuInfoEntity sku = skuInfoService.getById(skuId);
        if (sku == null) {
            return null;
        }
        return toResponse(sku);
    }

    @Transactional(rollbackFor = Exception.class)
    public MerchantProductResponse createProduct(MerchantProductUpdateRequest request) {
        validateRequest(request);

        Long categoryId = resolveCategoryId(request.getCategory(), null);
        String status = normalizeStatus(request.getStatus());
        String title = request.getTitle().trim();
        String coverUrl = trim(request.getCoverUrl());
        String subtitle = joinSellingPoints(request.getSellingPoints());
        Date now = new Date();

        SpuInfoEntity spu = new SpuInfoEntity();
        spu.setSpuName(title);
        spu.setSpuDescription(subtitle);
        spu.setCatalogId(categoryId);
        spu.setBrandId(0L);
        spu.setWeight(BigDecimal.ZERO);
        spu.setPublishStatus(STATUS_READY.equals(status) ? 1 : 0);
        spu.setCreateTime(now);
        spu.setUpdateTime(now);
        spuInfoService.save(spu);

        SkuInfoEntity sku = new SkuInfoEntity();
        sku.setSpuId(spu.getId());
        sku.setSkuTitle(title);
        sku.setSkuName(title);
        sku.setCatalogId(categoryId);
        sku.setBrandId(spu.getBrandId());
        sku.setPrice(request.getPrice().setScale(2, BigDecimal.ROUND_HALF_UP));
        sku.setSkuSubtitle(subtitle);
        sku.setSkuDesc(subtitle);
        sku.setSkuDefaultImg(coverUrl);
        sku.setSaleCount(0L);
        skuInfoService.save(sku);

        MerchantProductResponse response = toResponse(sku);
        response.setStatus(status);
        return response;
    }

    @Transactional(rollbackFor = Exception.class)
    public MerchantProductResponse updateProduct(Long skuId, MerchantProductUpdateRequest request) {
        validateSkuId(skuId);
        validateRequest(request);

        SkuInfoEntity sku = skuInfoService.getById(skuId);
        if (sku == null) {
            throw new IllegalArgumentException("商品不存在");
        }

        Long categoryId = resolveCategoryId(request.getCategory(), sku.getCatalogId());
        String status = normalizeStatus(request.getStatus());
        String title = request.getTitle().trim();
        String coverUrl = trim(request.getCoverUrl());
        String subtitle = joinSellingPoints(request.getSellingPoints());
        SpuInfoEntity spu = resolveOrCreateSpu(sku, title, categoryId, subtitle, status);

        sku.setSkuTitle(title);
        sku.setSkuName(title);
        if (spu != null && spu.getId() != null) {
            sku.setSpuId(spu.getId());
        }
        sku.setCatalogId(categoryId);
        sku.setPrice(request.getPrice().setScale(2, BigDecimal.ROUND_HALF_UP));
        sku.setSkuSubtitle(subtitle);
        sku.setSkuDesc(subtitle);
        sku.setSkuDefaultImg(coverUrl);
        skuInfoService.updateById(sku);

        if (spu != null) {
            spu.setSpuName(title);
            spu.setSpuDescription(subtitle);
            spu.setCatalogId(categoryId);
            spu.setPublishStatus(STATUS_READY.equals(status) ? 1 : 0);
            spu.setUpdateTime(new Date());
            spuInfoService.updateById(spu);
        }

        return getProduct(skuId);
    }

    private MerchantProductResponse toResponse(SkuInfoEntity sku) {
        MerchantProductResponse response = new MerchantProductResponse();
        response.setId(sku.getSkuId());
        response.setTitle(firstNonBlank(sku.getSkuTitle(), sku.getSkuName(), "未命名商品"));
        response.setCategory(resolveCategoryName(sku.getCatalogId()));
        response.setPrice(defaultPrice(sku.getPrice()));
        response.setSellingPoints(parseSellingPoints(sku.getSkuSubtitle(), sku.getSkuDesc()));
        response.setCoverUrl(firstNonBlank(sku.getSkuDefaultImg(), ""));
        response.setStatus(resolveStatus(sku.getSkuId()));
        return response;
    }

    private String resolveStatus(Long skuId) {
        if (skuId == null) {
            return STATUS_READY;
        }
        SpuInfoEntity spu = safeGetSpuInfoBySkuId(skuId);
        return spu == null || spu.getPublishStatus() == null || spu.getPublishStatus() != 0 ? STATUS_READY : STATUS_DRAFT;
    }

    private SpuInfoEntity safeGetSpuInfoBySkuId(Long skuId) {
        try {
            return spuInfoService.getSpuInfoBySkuId(skuId);
        } catch (RuntimeException ex) {
            log.warn("Merchant product spu fallback triggered for skuId={}", skuId, ex);
            return null;
        }
    }

    private String resolveCategoryName(Long categoryId) {
        if (categoryId == null) {
            return "未分类";
        }
        CategoryEntity category = categoryService.getById(categoryId);
        if (category == null || trim(category.getName()).isEmpty()) {
            return String.valueOf(categoryId);
        }
        return trim(category.getName());
    }

    private Long resolveCategoryId(String categoryName, Long fallbackCategoryId) {
        String normalized = trim(categoryName);
        if (normalized.isEmpty()) {
            return fallbackCategoryId;
        }
        List<CategoryEntity> categories = categoryService.list(new QueryWrapper<CategoryEntity>().eq("name", normalized).last("limit 1"));
        if (categories == null || categories.isEmpty()) {
            throw new IllegalArgumentException("分类不存在: " + normalized);
        }
        return categories.get(0).getCatId();
    }

    private SpuInfoEntity resolveOrCreateSpu(SkuInfoEntity sku, String title, Long categoryId, String subtitle, String status) {
        SpuInfoEntity spu = safeGetSpuInfoBySkuId(sku.getSkuId());
        if (spu != null) {
            return spu;
        }

        Date now = new Date();
        SpuInfoEntity created = new SpuInfoEntity();
        created.setSpuName(title);
        created.setSpuDescription(subtitle);
        created.setCatalogId(categoryId);
        created.setBrandId(sku.getBrandId() == null ? 0L : sku.getBrandId());
        created.setWeight(BigDecimal.ZERO);
        created.setPublishStatus(STATUS_READY.equals(status) ? 1 : 0);
        created.setCreateTime(now);
        created.setUpdateTime(now);
        spuInfoService.save(created);
        return created;
    }

    private List<String> parseSellingPoints(String subtitle, String description) {
        String source = trim(subtitle);
        if (source.isEmpty()) {
            source = trim(description);
        }
        if (source.isEmpty()) {
            return Collections.emptyList();
        }
        String[] parts = source.split("[\\n,，;；|]+");
        List<String> points = new ArrayList<String>();
        for (String part : parts) {
            String value = trim(part);
            if (!value.isEmpty()) {
                points.add(value);
            }
        }
        return points;
    }

    private String joinSellingPoints(List<String> sellingPoints) {
        if (sellingPoints == null || sellingPoints.isEmpty()) {
            return "";
        }
        List<String> normalized = new ArrayList<String>();
        for (String item : sellingPoints) {
            String value = trim(item);
            if (!value.isEmpty()) {
                normalized.add(value);
            }
        }
        return String.join(" | ", normalized);
    }

    private void validateSkuId(Long skuId) {
        if (skuId == null || skuId <= 0) {
            throw new IllegalArgumentException("skuId 非法");
        }
    }

    private void validateRequest(MerchantProductUpdateRequest request) {
        if (request == null) {
            throw new IllegalArgumentException("更新请求不能为空");
        }
        if (trim(request.getTitle()).isEmpty()) {
            throw new IllegalArgumentException("商品标题不能为空");
        }
        if (trim(request.getTitle()).length() > 120) {
            throw new IllegalArgumentException("商品标题不能超过 120 个字符");
        }
        if (trim(request.getCategory()).isEmpty()) {
            throw new IllegalArgumentException("商品分类不能为空");
        }
        if (request.getPrice() == null || request.getPrice().compareTo(BigDecimal.ZERO) < 0) {
            throw new IllegalArgumentException("商品价格不能小于 0");
        }
        String status = normalizeStatus(request.getStatus());
        if (!STATUS_DRAFT.equals(status) && !STATUS_READY.equals(status)) {
            throw new IllegalArgumentException("商品状态非法");
        }
        if (request.getSellingPoints() != null && request.getSellingPoints().size() > 8) {
            throw new IllegalArgumentException("卖点不能超过 8 条");
        }
        if (trim(request.getCoverUrl()).length() > 255) {
            throw new IllegalArgumentException("商品封面地址不能超过 255 个字符");
        }
    }

    private BigDecimal defaultPrice(BigDecimal price) {
        return price == null ? BigDecimal.ZERO : price.setScale(2, BigDecimal.ROUND_HALF_UP);
    }

    private String normalizeStatus(String status) {
        String normalized = trim(status);
        return normalized.isEmpty() ? STATUS_READY : normalized;
    }

    private String trim(String value) {
        return value == null ? "" : value.trim();
    }

    private String firstNonBlank(String... values) {
        if (values == null) {
            return "";
        }
        for (String value : values) {
            String normalized = trim(value);
            if (!normalized.isEmpty()) {
                return normalized;
            }
        }
        return "";
    }
}





