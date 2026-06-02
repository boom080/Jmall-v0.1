package com.shf.gulimall.order.app.service;

import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

@Component
public class JrunmallSeckillRetryScheduler {

    private final JrunmallSeckillStreamConsumerService consumerService;

    public JrunmallSeckillRetryScheduler(JrunmallSeckillStreamConsumerService consumerService) {
        this.consumerService = consumerService;
    }

    @Scheduled(fixedDelayString = "${jrunmall.seckill.consume-interval-ms:2000}")
    public void consumeNewMessages() {
        consumerService.consumeOnce();
    }

    @Scheduled(fixedDelayString = "${jrunmall.seckill.retry-interval-ms:30000}")
    public void retryPendingMessages() {
        consumerService.retryPendingOnce();
    }
}





