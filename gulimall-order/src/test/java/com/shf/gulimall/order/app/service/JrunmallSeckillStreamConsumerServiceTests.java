package com.shf.gulimall.order.app.service;

import com.shf.gulimall.order.config.JrunmallSeckillProperties;
import io.lettuce.core.StreamMessage;
import org.junit.Before;
import org.junit.Test;
import org.springframework.data.redis.core.RedisCallback;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.ValueOperations;

import java.util.LinkedHashMap;
import java.util.Collections;
import java.util.List;
import java.util.Map;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.atLeast;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

public class JrunmallSeckillStreamConsumerServiceTests {

    private StringRedisTemplate stringRedisTemplate;
    private JrunmallSeckillOrderService orderService;
    private JrunmallSeckillStreamConsumerService service;

    @Before
    public void setUp() {
        stringRedisTemplate = mock(StringRedisTemplate.class);
        orderService = mock(JrunmallSeckillOrderService.class);

        JrunmallSeckillProperties properties = new JrunmallSeckillProperties();
        properties.setMaxRetryCount(3);
        properties.setRetryCountKeyPrefix("jrunmall:seckill:retry");

        service = new JrunmallSeckillStreamConsumerService(stringRedisTemplate, orderService, properties);
    }

    @Test
    public void toEventMapsRedisStreamBody() {
        Map<String, String> body = new LinkedHashMap<String, String>();
        body.put("requestId", "req-1");
        body.put("userId", "900001");
        body.put("skuId", "14");
        body.put("quantity", "1");
        body.put("seckillSessionId", "flash-20260430");
        body.put("orderToken", "SEC-flash-20260430-req-1");
        body.put("timestamp", "2026-04-30T10:00:00Z");

        assertEquals(Long.valueOf(900001L), service.toEvent(body).getUserId());
        assertEquals("SEC-flash-20260430-req-1", service.toEvent(body).getOrderToken());
    }

    @Test
    public void shouldDeadLetterWhenRetryCountReachesThreshold() {
        assertFalse(service.shouldDeadLetter(2));
        assertTrue(service.shouldDeadLetter(3));
    }

    @Test
    public void consumeMessagesProcessesSuccessAndAck() {
        when(stringRedisTemplate.execute(any(RedisCallback.class))).thenReturn(null);
        List<StreamMessage<String, String>> messages = Collections.singletonList(buildRecord("177", "req-ok", "SEC-ok"));

        int consumed = service.consumeMessages(messages, false);

        assertEquals(1, consumed);
        verify(orderService).createSeckillOrder(any());
        verify(stringRedisTemplate, atLeast(1)).execute(any(RedisCallback.class));
    }

    @Test
    public void retryPendingMovesExceededMessageToDeadLetter() {
        ValueOperations<String, String> valueOperations = mock(ValueOperations.class);
        when(stringRedisTemplate.opsForValue()).thenReturn(valueOperations);
        when(valueOperations.increment(any())).thenReturn(3L);
        when(stringRedisTemplate.execute(any(RedisCallback.class))).thenReturn(null);
        when(orderService.createSeckillOrder(any())).thenThrow(new IllegalStateException("insert failed"));

        List<StreamMessage<String, String>> messages = Collections.singletonList(buildRecord("178", "req-dead", "SEC-dead"));
        int processed = service.consumeMessages(messages, true);

        assertEquals(1, processed);
        verify(valueOperations).increment(any());
        verify(stringRedisTemplate, atLeast(2)).execute(any(RedisCallback.class));
    }

    private StreamMessage<String, String> buildRecord(String id, String requestId, String orderToken) {
        Map<String, String> body = new LinkedHashMap<String, String>();
        body.put("requestId", requestId);
        body.put("userId", "900001");
        body.put("skuId", "14");
        body.put("quantity", "1");
        body.put("seckillSessionId", "flash-20260430");
        body.put("orderToken", orderToken);
        body.put("timestamp", "2026-04-30T10:00:00Z");
        return new StreamMessage<String, String>("jrunmall:seckill:orders", id, body);
    }
}





