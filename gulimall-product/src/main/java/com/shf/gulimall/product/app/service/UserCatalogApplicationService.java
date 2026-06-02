package com.shf.gulimall.product.app.service;

import com.shf.common.utils.PageUtils;
import com.shf.gulimall.product.app.dto.UserCatalogProductCardResponse;
import com.shf.gulimall.product.app.dto.UserCatalogProductDetailResponse;
import com.shf.gulimall.product.app.dto.UserCatalogProductPageResponse;
import com.shf.gulimall.product.entity.CategoryEntity;
import com.shf.gulimall.product.entity.SkuImagesEntity;
import com.shf.gulimall.product.entity.SkuInfoEntity;
import com.shf.gulimall.product.entity.SpuInfoDescEntity;
import com.shf.gulimall.product.entity.SpuInfoEntity;
import com.shf.gulimall.product.service.CategoryService;
import com.shf.gulimall.product.service.SkuInfoService;
import com.shf.gulimall.product.service.SpuInfoService;
import com.shf.gulimall.product.vo.AttrValueWithSkuIdVo;
import com.shf.gulimall.product.vo.SkuItemSaleAttrVo;
import com.shf.gulimall.product.vo.SkuItemVo;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ExecutionException;

@Service
public class UserCatalogApplicationService {

    private final SkuInfoService skuInfoService;
    private final CategoryService categoryService;
    private final SpuInfoService spuInfoService;

    public UserCatalogApplicationService(SkuInfoService skuInfoService, CategoryService categoryService, SpuInfoService spuInfoService) {
        this.skuInfoService = skuInfoService;
        this.categoryService = categoryService;
        this.spuInfoService = spuInfoService;
    }

    public UserCatalogProductPageResponse listProducts(Map<String, Object> params) {
        Map<String, Object> queryParams = new HashMap<>(params);
        queryParams.put("publishedOnly", "true");
        PageUtils page = skuInfoService.queryPageCondition(queryParams);
        List<UserCatalogProductCardResponse> items = new ArrayList<>();
        for (Object record : page.getList()) {
            if (record instanceof SkuInfoEntity) {
                items.add(toCardResponse((SkuInfoEntity) record));
            }
        }

        UserCatalogProductPageResponse response = new UserCatalogProductPageResponse();
        response.setItems(items);
        response.setTotalCount(page.getTotalCount());
        response.setPageSize(page.getPageSize());
        response.setCurrentPage(page.getCurrPage());
        response.setTotalPage(page.getTotalPage());
        return response;
    }

    public UserCatalogProductDetailResponse getProductDetail(Long skuId) throws ExecutionException, InterruptedException {
        if (!isPublishedSku(skuInfoService.getById(skuId))) {
            return null;
        }

        SkuItemVo item;
        try {
            item = skuInfoService.item(skuId);
        } catch (Exception ex) {
            if (ex instanceof InterruptedException) {
                Thread.currentThread().interrupt();
            }
            return getProductDetailFromSkuInfo(skuId);
        }
        if (item == null || item.getInfo() == null) {
            return getProductDetailFromSkuInfo(skuId);
        }

        SkuInfoEntity info = item.getInfo();
        if (!isPublishedSku(info)) {
            return null;
        }
        UserCatalogProductDetailResponse response = new UserCatalogProductDetailResponse();
        response.setId(info.getSkuId());
        response.setTitle(firstNonBlank(info.getSkuTitle(), info.getSkuName(), "未命名商品"));
        response.setCategory(resolveCategoryName(info.getCatalogId()));
        response.setSubtitle(firstNonBlank(info.getSkuSubtitle(), info.getSkuDesc(), "商品详情页聚合信息"));
        response.setPrice(info.getPrice());
        response.setCoverUrl(resolveCoverUrl(info, item.getImages()));
        response.setSummary(buildSummary(info, item.getDesc()));
        response.setDetail(buildDetail(item.getDesc(), info.getSkuDesc()));
        response.setImageUrls(resolveImageUrls(item.getImages(), response.getCoverUrl()));
        response.setSellingPoints(resolveSellingPoints(item.getSaleAttr(), info));
        response.setDetailAttributes(resolveDetailAttributes(item.getSaleAttr()));
        return response;
    }

    private UserCatalogProductDetailResponse getProductDetailFromSkuInfo(Long skuId) {
        if (skuId == null) {
            return null;
        }
        SkuInfoEntity info = skuInfoService.getById(skuId);
        if (info == null || !isPublishedSku(info)) {
            return null;
        }
        UserCatalogProductDetailResponse response = new UserCatalogProductDetailResponse();
        response.setId(info.getSkuId());
        response.setTitle(firstNonBlank(info.getSkuTitle(), info.getSkuName(), "未命名商品"));
        response.setCategory(resolveCategoryName(info.getCatalogId()));
        response.setSubtitle(firstNonBlank(info.getSkuSubtitle(), info.getSkuDesc(), "商品详情页聚合信息"));
        response.setPrice(info.getPrice());
        response.setCoverUrl(firstNonBlank(info.getSkuDefaultImg(), ""));
        response.setSummary(buildSummary(info, null));
        response.setDetail(firstNonBlank(info.getSkuDesc(), info.getSkuSubtitle(), "暂无更多商品详情"));
        response.setImageUrls(resolveImageUrls(Collections.<SkuImagesEntity>emptyList(), response.getCoverUrl()));
        response.setSellingPoints(resolveSellingPoints(Collections.<SkuItemSaleAttrVo>emptyList(), info));
        response.setDetailAttributes(Collections.<String>emptyList());
        return response;
    }

    private UserCatalogProductCardResponse toCardResponse(SkuInfoEntity entity) {
        UserCatalogProductCardResponse response = new UserCatalogProductCardResponse();
        response.setId(entity.getSkuId());
        response.setTitle(firstNonBlank(entity.getSkuTitle(), entity.getSkuName(), "未命名商品"));
        response.setCategory(resolveCategoryName(entity.getCatalogId()));
        response.setSubtitle(firstNonBlank(entity.getSkuSubtitle(), entity.getSkuDesc(), "真实商品列表"));
        response.setPrice(entity.getPrice());
        response.setCoverUrl(firstNonBlank(entity.getSkuDefaultImg(), ""));
        response.setSummary(buildSummary(entity, null));
        response.setSellingPoints(resolveSellingPoints(Collections.<SkuItemSaleAttrVo>emptyList(), entity));
        return response;
    }

    private String resolveCategoryName(Long catalogId) {
        if (catalogId == null) {
            return "未分类";
        }
        CategoryEntity category = categoryService.getById(catalogId);
        return category == null ? String.valueOf(catalogId) : firstNonBlank(category.getName(), String.valueOf(catalogId));
    }

    private String resolveCoverUrl(SkuInfoEntity info, List<SkuImagesEntity> images) {
        if (info != null && isNotBlank(info.getSkuDefaultImg())) {
            return info.getSkuDefaultImg().trim();
        }
        if (images != null) {
            for (SkuImagesEntity image : images) {
                if (image != null && Integer.valueOf(1).equals(image.getDefaultImg()) && isNotBlank(image.getImgUrl())) {
                    return image.getImgUrl().trim();
                }
            }
            for (SkuImagesEntity image : images) {
                if (image != null && isNotBlank(image.getImgUrl())) {
                    return image.getImgUrl().trim();
                }
            }
        }
        return "";
    }

    private List<String> resolveImageUrls(List<SkuImagesEntity> images, String coverUrl) {
        List<String> urls = new ArrayList<>();
        if (images != null) {
            for (SkuImagesEntity image : images) {
                if (image != null && isNotBlank(image.getImgUrl())) {
                    urls.add(image.getImgUrl().trim());
                }
            }
        }
        if (urls.isEmpty() && isNotBlank(coverUrl)) {
            urls.add(coverUrl.trim());
        }
        return urls;
    }

    private List<String> resolveSellingPoints(List<SkuItemSaleAttrVo> saleAttrs, SkuInfoEntity info) {
        List<String> result = new ArrayList<>();
        if (saleAttrs != null) {
            for (SkuItemSaleAttrVo saleAttr : saleAttrs) {
                if (saleAttr == null || !isNotBlank(saleAttr.getAttrName()) || saleAttr.getAttrValues() == null || saleAttr.getAttrValues().isEmpty()) {
                    continue;
                }
                AttrValueWithSkuIdVo attrValue = saleAttr.getAttrValues().get(0);
                if (attrValue != null && isNotBlank(attrValue.getAttrValue())) {
                    result.add(saleAttr.getAttrName().trim() + "：" + attrValue.getAttrValue().trim());
                }
                if (result.size() >= 3) {
                    break;
                }
            }
        }
        if (result.isEmpty()) {
            if (isNotBlank(info.getSkuSubtitle())) {
                result.add(info.getSkuSubtitle().trim());
            }
            if (isNotBlank(info.getSkuDesc())) {
                result.add(info.getSkuDesc().trim());
            }
        }
        if (result.isEmpty()) {
            result.add("真实商品接口已接通");
            result.add("支持图片字段回退");
        }
        return result;
    }

    private List<String> resolveDetailAttributes(List<SkuItemSaleAttrVo> saleAttrs) {
        List<String> result = new ArrayList<>();
        if (saleAttrs == null) {
            return result;
        }
        for (SkuItemSaleAttrVo saleAttr : saleAttrs) {
            if (saleAttr == null || !isNotBlank(saleAttr.getAttrName()) || saleAttr.getAttrValues() == null) {
                continue;
            }
            for (AttrValueWithSkuIdVo value : saleAttr.getAttrValues()) {
                if (value != null && isNotBlank(value.getAttrValue())) {
                    result.add(saleAttr.getAttrName().trim() + "：" + value.getAttrValue().trim());
                    break;
                }
            }
        }
        return result;
    }

    private String buildSummary(SkuInfoEntity info, SpuInfoDescEntity desc) {
        return firstNonBlank(
                info.getSkuSubtitle(),
                info.getSkuDesc(),
                desc == null ? null : desc.getDecript(),
                "真实商品接口聚合结果"
        );
    }

    private String buildDetail(SpuInfoDescEntity desc, String skuDesc) {
        return firstNonBlank(desc == null ? null : desc.getDecript(), skuDesc, "暂无更多商品详情");
    }

    private boolean isPublishedSku(SkuInfoEntity info) {
        if (info == null) {
            return false;
        }
        if (info.getSpuId() == null) {
            return true;
        }
        try {
            SpuInfoEntity spu = spuInfoService.getById(info.getSpuId());
            return spu == null || spu.getPublishStatus() == null || spu.getPublishStatus() != 0;
        } catch (RuntimeException ex) {
            return true;
        }
    }

    private boolean isNotBlank(String value) {
        return value != null && !value.trim().isEmpty();
    }

    private String firstNonBlank(String... values) {
        if (values == null) {
            return "";
        }
        for (String value : values) {
            if (isNotBlank(value)) {
                return value.trim();
            }
        }
        return "";
    }
}





