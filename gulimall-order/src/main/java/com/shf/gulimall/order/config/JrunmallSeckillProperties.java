package com.shf.gulimall.order.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@Component
@ConfigurationProperties(prefix = "jrunmall.seckill")
public class JrunmallSeckillProperties {

    private String streamName = "jrunmall:seckill:orders";
    private String consumerGroup = "jrunmall-order-group";
    private String consumerName = "jrunmall-order-local";
    private String deadLetterStreamName = "jrunmall:seckill:orders:dead";
    private String retryCountKeyPrefix = "jrunmall:seckill:retry";
    private Long demoUserId = 900001L;
    private long pendingIdleMs = 60000L;
    private long retryIntervalMs = 30000L;
    private int maxRetryCount = 3;

    public String getStreamName() {
        return streamName;
    }

    public void setStreamName(String streamName) {
        this.streamName = streamName;
    }

    public String getConsumerGroup() {
        return consumerGroup;
    }

    public void setConsumerGroup(String consumerGroup) {
        this.consumerGroup = consumerGroup;
    }

    public String getConsumerName() {
        return consumerName;
    }

    public void setConsumerName(String consumerName) {
        this.consumerName = consumerName;
    }

    public String getDeadLetterStreamName() {
        return deadLetterStreamName;
    }

    public void setDeadLetterStreamName(String deadLetterStreamName) {
        this.deadLetterStreamName = deadLetterStreamName;
    }

    public String getRetryCountKeyPrefix() {
        return retryCountKeyPrefix;
    }

    public void setRetryCountKeyPrefix(String retryCountKeyPrefix) {
        this.retryCountKeyPrefix = retryCountKeyPrefix;
    }

    public Long getDemoUserId() {
        return demoUserId;
    }

    public void setDemoUserId(Long demoUserId) {
        this.demoUserId = demoUserId;
    }

    public long getPendingIdleMs() {
        return pendingIdleMs;
    }

    public void setPendingIdleMs(long pendingIdleMs) {
        this.pendingIdleMs = pendingIdleMs;
    }

    public int getMaxRetryCount() {
        return maxRetryCount;
    }

    public void setMaxRetryCount(int maxRetryCount) {
        this.maxRetryCount = maxRetryCount;
    }

    public long getRetryIntervalMs() {
        return retryIntervalMs;
    }

    public void setRetryIntervalMs(long retryIntervalMs) {
        this.retryIntervalMs = retryIntervalMs;
    }
}





