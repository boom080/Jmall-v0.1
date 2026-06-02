package com.shf.gulimall.order.app;

import com.shf.gulimall.order.app.dto.MerchantSeckillOrderResponse;
import com.shf.gulimall.order.app.dto.UserSeckillOrderDetailResponse;
import com.shf.gulimall.order.app.service.JrunmallSeckillOrderService;
import com.shf.gulimall.order.app.service.JrunmallSeckillStreamConsumerService;
import com.shf.gulimall.order.config.JrunmallSeckillProperties;
import org.junit.Before;
import org.junit.Test;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import java.math.BigDecimal;
import java.util.Collections;

import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

public class JrunmallSeckillOrderControllerTests {

    private MockMvc mockMvc;
    private JrunmallSeckillStreamConsumerService streamConsumerService;
    private JrunmallSeckillOrderService orderService;
    private JrunmallSeckillProperties properties;

    @Before
    public void setUp() {
        streamConsumerService = mock(JrunmallSeckillStreamConsumerService.class);
        orderService = mock(JrunmallSeckillOrderService.class);
        properties = new JrunmallSeckillProperties();
        properties.setDemoUserId(900001L);
        mockMvc = MockMvcBuilders.standaloneSetup(new JrunmallSeckillOrderController(streamConsumerService, orderService, properties)).build();
    }

    @Test
    public void consumeOnceReturnsConsumedCount() throws Exception {
        when(streamConsumerService.consumeOnce()).thenReturn(1);

        mockMvc.perform(post("/order/seckill/streams/consume-once"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(0))
                .andExpect(jsonPath("$.consumed").value(1));
    }

    @Test
    public void retryPendingReturnsProcessedCount() throws Exception {
        when(streamConsumerService.retryPendingOnce()).thenReturn(2);

        mockMvc.perform(post("/order/seckill/streams/retry-pending"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(0))
                .andExpect(jsonPath("$.processed").value(2));
    }

    @Test
    public void listMerchantSeckillOrdersReturnsData() throws Exception {
        MerchantSeckillOrderResponse response = new MerchantSeckillOrderResponse();
        response.setOrderId(1L);
        response.setOrderSn("SEC202604300001");
        response.setUserId(900001L);
        response.setTitle("Jrunmall Phone");
        response.setQuantity(1);
        response.setStatus("CREATED");
        response.setSource("seckill");
        response.setTotalAmount(new BigDecimal("99.00"));

        when(orderService.listMerchantSeckillOrders()).thenReturn(Collections.singletonList(response));

        mockMvc.perform(get("/order/merchant/seckill-orders"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(0))
                .andExpect(jsonPath("$.data[0].orderSn").value("SEC202604300001"))
                .andExpect(jsonPath("$.data[0].source").value("seckill"));
    }

    @Test
    public void listInternalUserSeckillOrdersReturnsData() throws Exception {
        MerchantSeckillOrderResponse response = new MerchantSeckillOrderResponse();
        response.setOrderId(6L);
        response.setOrderSn("SEC20260501121222");
        response.setUserId(101L);
        response.setTitle("Jrun Phone 14");
        response.setQuantity(1);
        response.setStatus("CREATED");
        response.setSource("seckill");
        response.setTotalAmount(new BigDecimal("1999.00"));

        when(orderService.listUserSeckillOrders(101L)).thenReturn(Collections.singletonList(response));

        mockMvc.perform(get("/order/internal/seckill-orders/101"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(0))
                .andExpect(jsonPath("$.data[0].orderId").value(6))
                .andExpect(jsonPath("$.data[0].source").value("seckill"));
    }

    @Test
    public void getInternalUserSeckillOrderDetailReturnsData() throws Exception {
        UserSeckillOrderDetailResponse response = new UserSeckillOrderDetailResponse();
        response.setOrderId(6L);
        response.setOrderRef("seckill-6");
        response.setOrderSn("SEC20260501121222");
        response.setOrderSource("seckill");

        when(orderService.getUserSeckillOrderDetail(101L, 6L)).thenReturn(response);

        mockMvc.perform(get("/order/internal/seckill-orders/101/6"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(0))
                .andExpect(jsonPath("$.data.orderId").value(6))
                .andExpect(jsonPath("$.data.orderRef").value("seckill-6"))
                .andExpect(jsonPath("$.data.orderSource").value("seckill"));
    }
}





