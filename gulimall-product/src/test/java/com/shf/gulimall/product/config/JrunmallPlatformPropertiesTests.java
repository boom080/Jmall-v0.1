package com.shf.gulimall.product.config;

import org.junit.Test;

import static org.junit.Assert.assertEquals;

public class JrunmallPlatformPropertiesTests {

    @Test
    public void defaultsReflectMicroserviceBoundary() {
        JrunmallPlatformProperties properties = new JrunmallPlatformProperties();

        assertEquals("mysql", properties.getUserSide().getDatabase());
        assertEquals("redis", properties.getUserSide().getCache());
        assertEquals("http://127.0.0.1:19090", properties.getUserSide().getSeckillServiceUrl());
        assertEquals("postgresql", properties.getMerchantSide().getDatabase());
        assertEquals("redis", properties.getMerchantSide().getCache());
        assertEquals("redis-streams", properties.getMiddleware().getEventStream());
        assertEquals("jrunmall:seckill:orders", properties.getMiddleware().getSeckillStreamName());
        assertEquals("jrunmall-order-group", properties.getMiddleware().getSeckillConsumerGroup());
        assertEquals("jrunmall-product-local", properties.getMiddleware().getSeckillConsumerName());
    }
}





