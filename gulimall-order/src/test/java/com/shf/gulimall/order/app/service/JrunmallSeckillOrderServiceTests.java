package com.shf.gulimall.order.app.service;

import com.shf.gulimall.order.app.dto.MerchantSeckillOrderResponse;
import com.shf.gulimall.order.app.dto.SeckillOrderEvent;
import com.shf.gulimall.order.dao.JrunmallUserOrderDao;
import com.shf.gulimall.order.dao.JrunmallUserOrderItemDao;
import com.shf.gulimall.order.entity.JrunmallUserOrderEntity;
import com.shf.gulimall.order.entity.JrunmallUserOrderItemEntity;
import org.junit.Before;
import org.junit.Test;
import org.springframework.jdbc.core.JdbcTemplate;

import java.math.BigDecimal;
import java.util.Arrays;
import java.util.Collections;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.doAnswer;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

public class JrunmallSeckillOrderServiceTests {

    private JrunmallUserOrderDao userOrderDao;
    private JrunmallUserOrderItemDao userOrderItemDao;
    private JdbcTemplate jdbcTemplate;
    private JrunmallSeckillOrderService service;

    @Before
    public void setUp() {
        userOrderDao = mock(JrunmallUserOrderDao.class);
        userOrderItemDao = mock(JrunmallUserOrderItemDao.class);
        jdbcTemplate = mock(JdbcTemplate.class);
        service = new JrunmallSeckillOrderService(userOrderDao, userOrderItemDao, jdbcTemplate);
    }

    @Test
    public void createSeckillOrderReturnsExistingOrderWhenBizTokenExists() {
        SeckillOrderEvent event = buildEvent();
        JrunmallUserOrderEntity existing = new JrunmallUserOrderEntity();
        existing.setId(99L);
        existing.setBizToken(event.getOrderToken());

        when(userOrderDao.selectOne(any())).thenReturn(existing);

        JrunmallUserOrderEntity result = service.createSeckillOrder(event);

        assertEquals(Long.valueOf(99L), result.getId());
        verify(userOrderDao, never()).insert(any(JrunmallUserOrderEntity.class));
    }

    @Test
    public void createSeckillOrderCreatesOrderAndItem() {
        SeckillOrderEvent event = buildEvent();
        when(userOrderDao.selectOne(any())).thenReturn(null);
        when(jdbcTemplate.queryForList(anyString(), eq(14L))).thenReturn(Collections.singletonList(buildSkuRow()));
        doAnswer(invocation -> {
            JrunmallUserOrderEntity order = invocation.getArgument(0);
            order.setId(11L);
            return 1;
        }).when(userOrderDao).insert(any(JrunmallUserOrderEntity.class));

        JrunmallUserOrderEntity result = service.createSeckillOrder(event);

        assertEquals(Long.valueOf(11L), result.getId());
        assertEquals("seckill", result.getOrderSource());
        verify(userOrderItemDao).insert(any(JrunmallUserOrderItemEntity.class));
    }

    @Test
    public void listMerchantSeckillOrdersMapsSourceAndItemTitle() {
        JrunmallUserOrderEntity order = new JrunmallUserOrderEntity();
        order.setId(1L);
        order.setOrderSn("SEC202604300001");
        order.setUserId(900001L);
        order.setUsername("demo-user");
        order.setStatus("CREATED");
        order.setOrderSource("seckill");
        order.setTotalAmount(new BigDecimal("99.00"));
        order.setCreatedTime(new Date());

        JrunmallUserOrderItemEntity item = new JrunmallUserOrderItemEntity();
        item.setSkuId(14L);
        item.setTitle("Jrunmall Phone");
        item.setQuantity(1);

        when(userOrderDao.selectList(any())).thenReturn(Collections.singletonList(order));
        when(userOrderItemDao.selectList(any())).thenReturn(Collections.singletonList(item));

        List<MerchantSeckillOrderResponse> responses = service.listMerchantSeckillOrders();

        assertEquals(1, responses.size());
        assertEquals("seckill", responses.get(0).getSource());
        assertEquals("Jrunmall Phone", responses.get(0).getTitle());
    }

    private SeckillOrderEvent buildEvent() {
        SeckillOrderEvent event = new SeckillOrderEvent();
        event.setRequestId("req-1");
        event.setUserId(900001L);
        event.setSkuId(14L);
        event.setQuantity(1);
        event.setSeckillSessionId("flash-20260430");
        event.setOrderToken("SEC-flash-20260430-req-1");
        event.setTimestamp(new Date());
        return event;
    }

    private Map<String, Object> buildSkuRow() {
        Map<String, Object> row = new HashMap<String, Object>();
        row.put("spu_id", 101L);
        row.put("sku_name", "Jrunmall Phone");
        row.put("sku_title", "Jrunmall Phone 14");
        row.put("sku_subtitle", "Flash Sale");
        row.put("sku_desc", "Demo");
        row.put("sku_default_img", "/img/phone.png");
        row.put("price", new BigDecimal("99.00"));
        row.put("category_name", "Phone");
        return row;
    }
}





