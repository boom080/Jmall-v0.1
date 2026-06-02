package com.shf.gulimall.product.app;

import com.shf.gulimall.product.app.dto.UserCartItemResponse;
import com.shf.gulimall.product.app.dto.UserCartResponse;
import com.shf.gulimall.product.app.dto.UserOrderResponse;
import com.shf.gulimall.product.app.service.UserCommerceApplicationService;
import org.junit.Before;
import org.junit.Test;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import java.math.BigDecimal;
import java.util.Collections;
import java.util.Date;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.put;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

public class UserCommerceControllerTests {

    private MockMvc mockMvc;
    private UserCommerceApplicationService userCommerceApplicationService;

    @Before
    public void setUp() {
        userCommerceApplicationService = mock(UserCommerceApplicationService.class);
        mockMvc = MockMvcBuilders.standaloneSetup(
                new UserCommerceController(userCommerceApplicationService),
                new MerchantOrderController(userCommerceApplicationService)
        ).build();
    }

    @Test
    public void getCartItemsReturnsStructuredPayload() throws Exception {
        UserCartItemResponse item = new UserCartItemResponse();
        item.setSkuId(14L);
        item.setTitle("Jrun Phone 14");
        item.setQuantity(2);
        item.setPrice(new BigDecimal("1999.00"));
        item.setTotalAmount(new BigDecimal("3998.00"));

        UserCartResponse cart = new UserCartResponse();
        cart.setUserId(101L);
        cart.setDisplayName("Alice");
        cart.setTotalCount(2);
        cart.setTotalAmount(new BigDecimal("3998.00"));
        cart.setItems(Collections.singletonList(item));

        when(userCommerceApplicationService.getCart()).thenReturn(cart);

        mockMvc.perform(get("/product/user/cart/items"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(0))
                .andExpect(jsonPath("$.data.displayName").value("Alice"))
                .andExpect(jsonPath("$.data.items[0].title").value("Jrun Phone 14"));
    }

    @Test
    public void addCartItemReturnsValidationErrorWhenServiceRejects() throws Exception {
        when(userCommerceApplicationService.addCartItem(any())).thenThrow(new IllegalArgumentException("quantity 必须在 1 到 99 之间"));

        mockMvc.perform(post("/product/user/cart/items")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"skuId\":14,\"quantity\":0}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(400))
                .andExpect(jsonPath("$.msg").value("quantity 必须在 1 到 99 之间"));
    }

    @Test
    public void updateCartItemReturnsStructuredPayload() throws Exception {
        UserCartResponse cart = new UserCartResponse();
        cart.setTotalCount(1);
        cart.setTotalAmount(new BigDecimal("1999.00"));

        when(userCommerceApplicationService.updateCartItem(eq(14L), any())).thenReturn(cart);

        mockMvc.perform(put("/product/user/cart/items/14")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"quantity\":1}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(0))
                .andExpect(jsonPath("$.data.totalAmount").value(1999.00));
    }

    @Test
    public void createOrderReturnsCreatedStatusAndAddressSnapshot() throws Exception {
        UserOrderResponse order = new UserOrderResponse();
        order.setOrderId(1L);
        order.setOrderSn("202604270001");
        order.setStatus("CREATED");
        order.setTotalAmount(new BigDecimal("1999.00"));
        order.setAddressId(5L);
        order.setReceiverName("Alice");
        order.setReceiverAddress("Shanghai Pudong Road 1");
        order.setCreatedTime(new Date());

        when(userCommerceApplicationService.createOrder(any())).thenReturn(order);

        mockMvc.perform(post("/product/user/orders")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"note\":\"demo\",\"addressId\":5}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(0))
                .andExpect(jsonPath("$.data.status").value("CREATED"))
                .andExpect(jsonPath("$.data.receiverName").value("Alice"));
    }

    @Test
    public void payOrderReturnsPaidStatus() throws Exception {
        UserOrderResponse order = new UserOrderResponse();
        order.setOrderId(1L);
        order.setStatus("PAID");
        order.setOrderSn("202604270001");

        when(userCommerceApplicationService.payOrder(1L)).thenReturn(order);

        mockMvc.perform(post("/product/user/orders/1/pay"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(0))
                .andExpect(jsonPath("$.data.status").value("PAID"));
    }

    @Test
    public void listAllOrdersReturnsUnifiedArray() throws Exception {
        UserOrderResponse order = new UserOrderResponse();
        order.setOrderId(6L);
        order.setOrderRef("seckill-6");
        order.setOrderSn("SEC-6");
        order.setOrderSource("seckill");

        when(userCommerceApplicationService.listAllOrders()).thenReturn(Collections.singletonList(order));

        mockMvc.perform(get("/product/user/orders/all"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(0))
                .andExpect(jsonPath("$.data[0].orderRef").value("seckill-6"))
                .andExpect(jsonPath("$.data[0].orderSource").value("seckill"));
    }

    @Test
    public void getOrderByRefReturnsUnifiedDetail() throws Exception {
        UserOrderResponse order = new UserOrderResponse();
        order.setOrderId(6L);
        order.setOrderRef("seckill-6");
        order.setOrderSn("SEC-6");
        order.setOrderSource("seckill");

        when(userCommerceApplicationService.getOrderByRef("seckill-6")).thenReturn(order);

        mockMvc.perform(get("/product/user/orders/all/seckill-6"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(0))
                .andExpect(jsonPath("$.data.orderRef").value("seckill-6"))
                .andExpect(jsonPath("$.data.orderSource").value("seckill"));
    }

    @Test
    public void userSeckillOrdersReturnsArray() throws Exception {
        when(userCommerceApplicationService.listCurrentUserSeckillOrders()).thenReturn(Collections.emptyList());

        mockMvc.perform(get("/product/user/seckill-orders"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(0))
                .andExpect(jsonPath("$.data").isArray());
    }

    @Test
    public void merchantOrdersReturnsReadOnlyList() throws Exception {
        when(userCommerceApplicationService.listMerchantOrders()).thenReturn(Collections.emptyList());

        mockMvc.perform(get("/product/merchant/orders"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(0))
                .andExpect(jsonPath("$.data").isArray());
    }
}





