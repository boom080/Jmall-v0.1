package com.shf.gulimall.product.app.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.shf.gulimall.product.app.dto.MerchantProductResponse;
import com.shf.gulimall.product.app.dto.MerchantProductUpdateRequest;
import com.shf.gulimall.product.entity.CategoryEntity;
import com.shf.gulimall.product.entity.SkuInfoEntity;
import com.shf.gulimall.product.entity.SpuInfoEntity;
import com.shf.gulimall.product.service.CategoryService;
import com.shf.gulimall.product.service.SkuInfoService;
import com.shf.gulimall.product.service.SpuInfoService;
import org.junit.Before;
import org.junit.Test;
import org.mockito.ArgumentCaptor;

import java.math.BigDecimal;
import java.util.Arrays;
import java.util.Collections;

import static org.junit.Assert.assertEquals;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

public class MerchantProductApplicationServiceTests {

    private SkuInfoService skuInfoService;
    private SpuInfoService spuInfoService;
    private CategoryService categoryService;
    private MerchantProductApplicationService service;

    @Before
    public void setUp() {
        skuInfoService = mock(SkuInfoService.class);
        spuInfoService = mock(SpuInfoService.class);
        categoryService = mock(CategoryService.class);
        service = new MerchantProductApplicationService(skuInfoService, spuInfoService, categoryService);
    }

    @Test
    public void createProductPersistsSpuAndSku() {
        CategoryEntity category = new CategoryEntity();
        category.setCatId(225L);
        category.setName("手机数码");

        when(categoryService.list(any(QueryWrapper.class))).thenReturn(Collections.singletonList(category));
        when(categoryService.getById(225L)).thenReturn(category);
        when(spuInfoService.save(any(SpuInfoEntity.class))).thenAnswer(invocation -> {
            SpuInfoEntity spu = invocation.getArgument(0);
            spu.setId(1002L);
            return true;
        });
        when(skuInfoService.save(any(SkuInfoEntity.class))).thenAnswer(invocation -> {
            SkuInfoEntity sku = invocation.getArgument(0);
            sku.setSkuId(88L);
            return true;
        });

        MerchantProductUpdateRequest request = new MerchantProductUpdateRequest();
        request.setTitle("Jrun Pad Air");
        request.setCategory("手机数码");
        request.setPrice(new BigDecimal("1299.00"));
        request.setSellingPoints(Collections.singletonList("轻薄"));
        request.setCoverUrl("https://cdn.example.com/pad.png");
        request.setStatus("ready");

        MerchantProductResponse response = service.createProduct(request);

        ArgumentCaptor<SpuInfoEntity> spuCaptor = ArgumentCaptor.forClass(SpuInfoEntity.class);
        ArgumentCaptor<SkuInfoEntity> skuCaptor = ArgumentCaptor.forClass(SkuInfoEntity.class);
        verify(spuInfoService).save(spuCaptor.capture());
        verify(skuInfoService).save(skuCaptor.capture());

        assertEquals("Jrun Pad Air", spuCaptor.getValue().getSpuName());
        assertEquals(Integer.valueOf(1), spuCaptor.getValue().getPublishStatus());
        assertEquals(Long.valueOf(1002L), skuCaptor.getValue().getSpuId());
        assertEquals("轻薄", skuCaptor.getValue().getSkuSubtitle());
        assertEquals(Long.valueOf(88L), response.getId());
        assertEquals("ready", response.getStatus());
    }

    @Test
    public void updateProductSyncsSkuAndSpuFields() {
        SkuInfoEntity sku = new SkuInfoEntity();
        sku.setSkuId(14L);
        sku.setSpuId(1001L);
        sku.setCatalogId(225L);
        sku.setPrice(new BigDecimal("1999.00"));

        SpuInfoEntity spu = new SpuInfoEntity();
        spu.setId(1001L);
        spu.setPublishStatus(0);

        CategoryEntity category = new CategoryEntity();
        category.setCatId(225L);
        category.setName("手机数码");

        when(skuInfoService.getById(14L)).thenReturn(sku);
        when(spuInfoService.getSpuInfoBySkuId(14L)).thenReturn(spu);
        when(categoryService.list(any(QueryWrapper.class))).thenReturn(Collections.singletonList(category));
        when(skuInfoService.updateById(any(SkuInfoEntity.class))).thenReturn(true);
        when(spuInfoService.updateById(any(SpuInfoEntity.class))).thenReturn(true);

        MerchantProductUpdateRequest request = new MerchantProductUpdateRequest();
        request.setTitle("Jrun Phone 14 Pro");
        request.setCategory("手机数码");
        request.setPrice(new BigDecimal("2999.00"));
        request.setSellingPoints(Arrays.asList("轻旗舰", "长续航"));
        request.setCoverUrl("https://cdn.example.com/p14.png");
        request.setStatus("ready");

        service.updateProduct(14L, request);

        ArgumentCaptor<SkuInfoEntity> skuCaptor = ArgumentCaptor.forClass(SkuInfoEntity.class);
        ArgumentCaptor<SpuInfoEntity> spuCaptor = ArgumentCaptor.forClass(SpuInfoEntity.class);
        verify(skuInfoService).updateById(skuCaptor.capture());
        verify(spuInfoService).updateById(spuCaptor.capture());

        assertEquals("Jrun Phone 14 Pro", skuCaptor.getValue().getSkuTitle());
        assertEquals("https://cdn.example.com/p14.png", skuCaptor.getValue().getSkuDefaultImg());
        assertEquals("轻旗舰 | 长续航", skuCaptor.getValue().getSkuSubtitle());
        assertEquals(Integer.valueOf(1), spuCaptor.getValue().getPublishStatus());
    }

    @Test
    public void updateProductCreatesSpuWhenLegacySkuHasNoSpuRecord() {
        SkuInfoEntity sku = new SkuInfoEntity();
        sku.setSkuId(15L);
        sku.setCatalogId(225L);
        sku.setBrandId(12L);
        sku.setPrice(new BigDecimal("1999.00"));

        CategoryEntity category = new CategoryEntity();
        category.setCatId(225L);
        category.setName("手机数码");

        when(skuInfoService.getById(15L)).thenReturn(sku);
        when(spuInfoService.getSpuInfoBySkuId(15L)).thenReturn(null);
        when(categoryService.list(any(QueryWrapper.class))).thenReturn(Collections.singletonList(category));
        when(spuInfoService.save(any(SpuInfoEntity.class))).thenAnswer(invocation -> {
            SpuInfoEntity spu = invocation.getArgument(0);
            spu.setId(1003L);
            return true;
        });
        when(skuInfoService.updateById(any(SkuInfoEntity.class))).thenReturn(true);
        when(spuInfoService.updateById(any(SpuInfoEntity.class))).thenReturn(true);

        MerchantProductUpdateRequest request = new MerchantProductUpdateRequest();
        request.setTitle("Jrun Phone Legacy");
        request.setCategory("手机数码");
        request.setPrice(new BigDecimal("1999.00"));
        request.setSellingPoints(Collections.singletonList("轻旗舰"));
        request.setCoverUrl("");
        request.setStatus("draft");

        service.updateProduct(15L, request);

        ArgumentCaptor<SkuInfoEntity> skuCaptor = ArgumentCaptor.forClass(SkuInfoEntity.class);
        ArgumentCaptor<SpuInfoEntity> spuCaptor = ArgumentCaptor.forClass(SpuInfoEntity.class);
        verify(skuInfoService).updateById(skuCaptor.capture());
        verify(spuInfoService).save(spuCaptor.capture());

        assertEquals(Long.valueOf(1003L), skuCaptor.getValue().getSpuId());
        assertEquals(Integer.valueOf(0), spuCaptor.getValue().getPublishStatus());
    }

    @Test
    public void listProductsFallsBackWhenSpuQueryFails() {
        SkuInfoEntity sku = new SkuInfoEntity();
        sku.setSkuId(14L);
        sku.setSkuTitle("Jrun Phone 14");
        sku.setSkuName("Jrun Phone 14");
        sku.setCatalogId(225L);
        sku.setPrice(new BigDecimal("1999.00"));
        sku.setSkuSubtitle("轻量 | 透气");
        sku.setSkuDefaultImg("");

        CategoryEntity category = new CategoryEntity();
        category.setCatId(225L);
        category.setName("手机数码");

        when(skuInfoService.list(any(QueryWrapper.class))).thenReturn(Collections.singletonList(sku));
        when(categoryService.getById(225L)).thenReturn(category);
        when(spuInfoService.getSpuInfoBySkuId(14L)).thenThrow(new RuntimeException("table missing"));

        assertEquals(1, service.listProducts().getItems().size());
        assertEquals("ready", service.listProducts().getItems().get(0).getStatus());
    }

    @Test(expected = IllegalArgumentException.class)
    public void updateProductRejectsInvalidStatus() {
        MerchantProductUpdateRequest request = new MerchantProductUpdateRequest();
        request.setTitle("Jrun Phone 14 Pro");
        request.setCategory("手机数码");
        request.setPrice(new BigDecimal("2999.00"));
        request.setStatus("unknown");

        service.updateProduct(14L, request);
    }
}





