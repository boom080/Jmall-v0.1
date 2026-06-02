package com.shf.gulimall.product.app.service;

import com.shf.common.utils.PageUtils;
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
import java.util.Collections;
import java.util.HashMap;
import java.util.Map;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNull;
import static org.mockito.ArgumentMatchers.anyMap;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

public class UserCatalogApplicationServiceTests {

    private SkuInfoService skuInfoService;
    private CategoryService categoryService;
    private SpuInfoService spuInfoService;
    private UserCatalogApplicationService service;

    @Before
    public void setUp() {
        skuInfoService = mock(SkuInfoService.class);
        categoryService = mock(CategoryService.class);
        spuInfoService = mock(SpuInfoService.class);
        service = new UserCatalogApplicationService(skuInfoService, categoryService, spuInfoService);
    }

    @Test
    public void listProductsRequestsPublishedOnlySkus() {
        SkuInfoEntity sku = new SkuInfoEntity();
        sku.setSkuId(14L);
        sku.setSkuTitle("Jrun Phone 14");
        sku.setCatalogId(225L);
        sku.setPrice(new BigDecimal("1999.00"));

        CategoryEntity category = new CategoryEntity();
        category.setCatId(225L);
        category.setName("手机数码");

        when(skuInfoService.queryPageCondition(anyMap())).thenReturn(new PageUtils(Collections.singletonList(sku), 1, 10, 1));
        when(categoryService.getById(225L)).thenReturn(category);

        Map<String, Object> params = new HashMap<String, Object>();
        params.put("page", "1");
        service.listProducts(params);

        ArgumentCaptor<Map> captor = ArgumentCaptor.forClass(Map.class);
        org.mockito.Mockito.verify(skuInfoService).queryPageCondition(captor.capture());
        assertEquals("true", captor.getValue().get("publishedOnly"));
    }

    @Test
    public void productDetailReturnsNullWhenSkuIsExplicitlyUnpublished() throws Exception {
        SkuInfoEntity sku = new SkuInfoEntity();
        sku.setSkuId(14L);
        sku.setSpuId(1001L);

        SpuInfoEntity spu = new SpuInfoEntity();
        spu.setId(1001L);
        spu.setPublishStatus(0);

        when(skuInfoService.getById(14L)).thenReturn(sku);
        when(spuInfoService.getById(1001L)).thenReturn(spu);

        assertNull(service.getProductDetail(14L));
    }
}
