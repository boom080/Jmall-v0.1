package com.shf.gulimall.product.app;

import com.shf.gulimall.product.app.dto.SeckillDealResponse;
import com.shf.gulimall.product.app.dto.SeckillSubmitPublicResponse;
import com.shf.gulimall.product.app.service.UserSeckillApplicationService;
import org.junit.Before;
import org.junit.Test;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

public class UserSeckillControllerTests {

    private MockMvc mockMvc;
    private UserSeckillApplicationService userSeckillApplicationService;

    @Before
    public void setUp() {
        userSeckillApplicationService = mock(UserSeckillApplicationService.class);
        mockMvc = MockMvcBuilders.standaloneSetup(new UserSeckillController(userSeckillApplicationService)).build();
    }

    @Test
    public void currentDealReturnsPublicProductInfo() throws Exception {
        SeckillDealResponse response = new SeckillDealResponse();
        response.setTitle("Jrun Phone 14");
        response.setCategory("手机数码");
        response.setLimitPerOrder(1);

        when(userSeckillApplicationService.currentDeal()).thenReturn(response);

        mockMvc.perform(get("/product/user/seckill/current"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(0))
                .andExpect(jsonPath("$.data.title").value("Jrun Phone 14"))
                .andExpect(jsonPath("$.data.skuId").doesNotExist());
    }

    @Test
    public void submitReturnsAcceptedResult() throws Exception {
        SeckillSubmitPublicResponse response = new SeckillSubmitPublicResponse();
        response.setAccepted(true);
        response.setCode("ACCEPTED");
        response.setMessage("抢购成功，请继续确认收货地址并完成支付。");
        response.setOrderId(8L);
        response.setOrderRef("8");

        when(userSeckillApplicationService.submit(any())).thenReturn(response);

        mockMvc.perform(post("/product/user/seckill/submit")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"quantity\":1}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(0))
                .andExpect(jsonPath("$.data.accepted").value(true))
                .andExpect(jsonPath("$.data.orderId").value(8))
                .andExpect(jsonPath("$.data.orderToken").doesNotExist());
    }

    @Test
    public void submitReturnsUnauthorizedWhenUserMissing() throws Exception {
        when(userSeckillApplicationService.submit(any())).thenThrow(new IllegalStateException("请先登录"));

        mockMvc.perform(post("/product/user/seckill/submit")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"quantity\":1}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(401))
                .andExpect(jsonPath("$.msg").value("请先登录"));
    }

    @Test
    public void consumeOnceReturnsGoneMessage() throws Exception {
        mockMvc.perform(post("/product/user/seckill/consume-once"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(410))
                .andExpect(jsonPath("$.msg").exists());
    }
}





