package com.shf.gulimall.product.app;

import com.shf.gulimall.product.app.dto.MerchantProductListResponse;
import com.shf.gulimall.product.app.dto.MerchantProductResponse;
import com.shf.gulimall.product.app.dto.MerchantImageUploadResponse;
import com.shf.gulimall.product.app.service.MerchantProductApplicationService;
import com.shf.gulimall.product.app.service.MerchantProductImageStorageService;
import org.junit.Before;
import org.junit.Test;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.mock.web.MockMultipartFile;

import java.math.BigDecimal;
import java.util.Collections;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.put;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

public class MerchantProductControllerTests {

    private MockMvc mockMvc;
    private MerchantProductApplicationService merchantProductApplicationService;
    private MerchantProductImageStorageService merchantProductImageStorageService;

    @Before
    public void setUp() {
        merchantProductApplicationService = mock(MerchantProductApplicationService.class);
        merchantProductImageStorageService = mock(MerchantProductImageStorageService.class);
        mockMvc = MockMvcBuilders.standaloneSetup(
                new MerchantProductController(merchantProductApplicationService, merchantProductImageStorageService)
        ).build();
    }

    @Test
    public void listProductsReturnsItems() throws Exception {
        MerchantProductResponse item = new MerchantProductResponse();
        item.setId(14L);
        item.setTitle("Jrun Phone 14");
        item.setCategory("手机数码");
        item.setPrice(new BigDecimal("1999.00"));
        item.setStatus("ready");

        MerchantProductListResponse response = new MerchantProductListResponse();
        response.setItems(Collections.singletonList(item));

        when(merchantProductApplicationService.listProducts()).thenReturn(response);

        mockMvc.perform(get("/product/merchant/products"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(0))
                .andExpect(jsonPath("$.data.items[0].id").value(14))
                .andExpect(jsonPath("$.data.items[0].status").value("ready"));
    }

    @Test
    public void getProductReturnsDetail() throws Exception {
        MerchantProductResponse item = new MerchantProductResponse();
        item.setId(14L);
        item.setTitle("Jrun Phone 14");
        item.setCategory("手机数码");
        item.setPrice(new BigDecimal("1999.00"));
        item.setStatus("ready");

        when(merchantProductApplicationService.getProduct(14L)).thenReturn(item);

        mockMvc.perform(get("/product/merchant/products/14"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(0))
                .andExpect(jsonPath("$.data.title").value("Jrun Phone 14"));
    }

    @Test
    public void createProductReturnsCreatedData() throws Exception {
        MerchantProductResponse item = new MerchantProductResponse();
        item.setId(88L);
        item.setTitle("Jrun Pad Air");
        item.setCategory("手机数码");
        item.setPrice(new BigDecimal("1299.00"));
        item.setStatus("draft");

        when(merchantProductApplicationService.createProduct(any())).thenReturn(item);

        mockMvc.perform(post("/product/merchant/products")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"title\":\"Jrun Pad Air\",\"category\":\"手机数码\",\"price\":1299,\"sellingPoints\":[\"轻薄\"],\"coverUrl\":\"\",\"status\":\"draft\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(0))
                .andExpect(jsonPath("$.data.id").value(88))
                .andExpect(jsonPath("$.data.title").value("Jrun Pad Air"));
    }

    @Test
    public void createProductReturnsValidationErrorWhenRejected() throws Exception {
        when(merchantProductApplicationService.createProduct(any()))
                .thenThrow(new IllegalArgumentException("商品分类不能为空"));

        mockMvc.perform(post("/product/merchant/products")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"title\":\"Jrun Pad Air\",\"category\":\"\",\"price\":1299,\"sellingPoints\":[],\"coverUrl\":\"\",\"status\":\"draft\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(400))
                .andExpect(jsonPath("$.msg").value("商品分类不能为空"));
    }

    @Test
    public void updateProductReturnsValidationErrorWhenRejected() throws Exception {
        when(merchantProductApplicationService.updateProduct(org.mockito.Mockito.eq(14L), any()))
                .thenThrow(new IllegalArgumentException("商品标题不能为空"));

        mockMvc.perform(put("/product/merchant/products/14")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"title\":\"\",\"category\":\"手机数码\",\"price\":1999,\"sellingPoints\":[],\"coverUrl\":\"\",\"status\":\"ready\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(400))
                .andExpect(jsonPath("$.msg").value("商品标题不能为空"));
    }

    @Test
    public void updateProductReturnsUpdatedData() throws Exception {
        MerchantProductResponse item = new MerchantProductResponse();
        item.setId(14L);
        item.setTitle("Jrun Phone 14 Pro");
        item.setCategory("手机数码");
        item.setPrice(new BigDecimal("2999.00"));
        item.setStatus("ready");

        when(merchantProductApplicationService.updateProduct(org.mockito.Mockito.eq(14L), any())).thenReturn(item);

        mockMvc.perform(put("/product/merchant/products/14")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"title\":\"Jrun Phone 14 Pro\",\"category\":\"手机数码\",\"price\":2999,\"sellingPoints\":[\"轻旗舰\"],\"coverUrl\":\"\",\"status\":\"ready\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(0))
                .andExpect(jsonPath("$.data.title").value("Jrun Phone 14 Pro"))
                .andExpect(jsonPath("$.data.price").value(2999.00));
    }

    @Test
    public void uploadImageReturnsUploadedUrl() throws Exception {
        MerchantImageUploadResponse response = new MerchantImageUploadResponse();
        response.setObjectKey("merchant-products/demo.png");
        response.setUrl("https://cdn.example.com/merchant-products/demo.png");
        when(merchantProductImageStorageService.uploadProductImage(any())).thenReturn(response);

        MockMultipartFile file = new MockMultipartFile(
                "file",
                "demo.png",
                "image/png",
                "demo".getBytes()
        );

        mockMvc.perform(org.springframework.test.web.servlet.request.MockMvcRequestBuilders.multipart("/product/merchant/products/upload-image")
                        .file(file))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(0))
                .andExpect(jsonPath("$.data.objectKey").value("merchant-products/demo.png"));
    }

    @Test
    public void uploadImageReturnsConfigurationErrorWhenOssMissing() throws Exception {
        when(merchantProductImageStorageService.uploadProductImage(any()))
                .thenThrow(new IllegalStateException("OSS 未配置。请先在根目录 .env.local 中填写 JRUNMALL_OSS_* 变量，未配置前仍可手动编辑图片 URL。"));

        MockMultipartFile file = new MockMultipartFile(
                "file",
                "demo.png",
                "image/png",
                "demo".getBytes()
        );

        mockMvc.perform(org.springframework.test.web.servlet.request.MockMvcRequestBuilders.multipart("/product/merchant/products/upload-image")
                        .file(file))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(503))
                .andExpect(jsonPath("$.msg").value(org.hamcrest.Matchers.containsString("OSS 未配置")));
    }
}





