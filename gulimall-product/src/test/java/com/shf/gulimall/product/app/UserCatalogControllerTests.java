package com.shf.gulimall.product.app;

import com.shf.gulimall.product.app.dto.UserCatalogProductCardResponse;
import com.shf.gulimall.product.app.dto.UserCatalogProductDetailResponse;
import com.shf.gulimall.product.app.dto.UserCatalogProductPageResponse;
import com.shf.gulimall.product.app.service.UserCatalogApplicationService;
import org.junit.Before;
import org.junit.Test;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import java.math.BigDecimal;
import java.util.Collections;

import static org.mockito.ArgumentMatchers.anyMap;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

public class UserCatalogControllerTests {

    private MockMvc mockMvc;
    private UserCatalogApplicationService userCatalogApplicationService;

    @Before
    public void setUp() {
        userCatalogApplicationService = mock(UserCatalogApplicationService.class);
        UserCatalogController controller = new UserCatalogController(userCatalogApplicationService);
        mockMvc = MockMvcBuilders.standaloneSetup(controller).build();
    }

    @Test
    public void listProductsReturnsStructuredCatalogPayload() throws Exception {
        UserCatalogProductCardResponse item = new UserCatalogProductCardResponse();
        item.setId(1L);
        item.setTitle("Jrun Air 14");
        item.setCategory("电脑办公");
        item.setPrice(new BigDecimal("5699"));
        item.setCoverUrl("http://img.local/1.jpg");

        UserCatalogProductPageResponse page = new UserCatalogProductPageResponse();
        page.setItems(Collections.singletonList(item));
        page.setCurrentPage(1);
        page.setPageSize(12);
        page.setTotalCount(1);
        page.setTotalPage(1);

        when(userCatalogApplicationService.listProducts(anyMap())).thenReturn(page);

        mockMvc.perform(get("/product/user/catalog/products?page=1&limit=12"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(0))
                .andExpect(jsonPath("$.data.items[0].title").value("Jrun Air 14"))
                .andExpect(jsonPath("$.data.items[0].category").value("电脑办公"));
    }

    @Test
    public void productDetailReturnsStructuredPayload() throws Exception {
        UserCatalogProductDetailResponse detail = new UserCatalogProductDetailResponse();
        detail.setId(1L);
        detail.setTitle("Jrun Air 14");
        detail.setCategory("电脑办公");
        detail.setPrice(new BigDecimal("5699"));
        detail.setCoverUrl("http://img.local/1.jpg");
        detail.setSummary("轻薄办公本");
        detail.setDetail("更详细的商品介绍");

        when(userCatalogApplicationService.getProductDetail(1L)).thenReturn(detail);

        mockMvc.perform(get("/product/user/catalog/products/1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(0))
                .andExpect(jsonPath("$.data.title").value("Jrun Air 14"))
                .andExpect(jsonPath("$.data.detail").value("更详细的商品介绍"));
    }
}





