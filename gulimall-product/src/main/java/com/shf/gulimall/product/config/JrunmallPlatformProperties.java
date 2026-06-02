package com.shf.gulimall.product.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@Component
@ConfigurationProperties(prefix = "jrunmall.platform")
public class JrunmallPlatformProperties {

    private final UserSide userSide = new UserSide();
    private final MerchantSide merchantSide = new MerchantSide();
    private final Middleware middleware = new Middleware();

    public UserSide getUserSide() {
        return userSide;
    }

    public MerchantSide getMerchantSide() {
        return merchantSide;
    }

    public Middleware getMiddleware() {
        return middleware;
    }

    public static class UserSide {
        private String database = "mysql";
        private String cache = "redis";
        private String seckillServiceUrl = "http://127.0.0.1:19090";
        private String seckillActivityId = "flash-20260429";
        private Long seckillSkuId = 14L;
        private Integer seckillLimitPerOrder = 1;
        private Integer seckillWarmupStock = 50;
        private Boolean seckillAutoWarmupOnSoldOut = true;

        public String getDatabase() {
            return database;
        }

        public void setDatabase(String database) {
            this.database = database;
        }

        public String getCache() {
            return cache;
        }

        public void setCache(String cache) {
            this.cache = cache;
        }

        public String getSeckillServiceUrl() {
            return seckillServiceUrl;
        }

        public void setSeckillServiceUrl(String seckillServiceUrl) {
            this.seckillServiceUrl = seckillServiceUrl;
        }

        public String getSeckillActivityId() {
            return seckillActivityId;
        }

        public void setSeckillActivityId(String seckillActivityId) {
            this.seckillActivityId = seckillActivityId;
        }

        public Long getSeckillSkuId() {
            return seckillSkuId;
        }

        public void setSeckillSkuId(Long seckillSkuId) {
            this.seckillSkuId = seckillSkuId;
        }

        public Integer getSeckillLimitPerOrder() {
            return seckillLimitPerOrder;
        }

        public void setSeckillLimitPerOrder(Integer seckillLimitPerOrder) {
            this.seckillLimitPerOrder = seckillLimitPerOrder;
        }

        public Integer getSeckillWarmupStock() {
            return seckillWarmupStock;
        }

        public void setSeckillWarmupStock(Integer seckillWarmupStock) {
            this.seckillWarmupStock = seckillWarmupStock;
        }

        public Boolean getSeckillAutoWarmupOnSoldOut() {
            return seckillAutoWarmupOnSoldOut;
        }

        public void setSeckillAutoWarmupOnSoldOut(Boolean seckillAutoWarmupOnSoldOut) {
            this.seckillAutoWarmupOnSoldOut = seckillAutoWarmupOnSoldOut;
        }
    }

    public static class MerchantSide {
        private String database = "postgresql";
        private String cache = "redis";
        private String reportingSchema = "jrunmall_merchant";

        public String getDatabase() {
            return database;
        }

        public void setDatabase(String database) {
            this.database = database;
        }

        public String getCache() {
            return cache;
        }

        public void setCache(String cache) {
            this.cache = cache;
        }

        public String getReportingSchema() {
            return reportingSchema;
        }

        public void setReportingSchema(String reportingSchema) {
            this.reportingSchema = reportingSchema;
        }
    }

    public static class Middleware {
        private String gateway = "jrunmall-gateway";
        private String contract = "rest-openapi";
        private String eventStream = "redis-streams";
        private String observability = "structured-logs";
        private String seckillStreamName = "jrunmall:seckill:orders";
        private String seckillConsumerGroup = "jrunmall-order-group";
        private String seckillConsumerName = "jrunmall-product-local";
        private String seckillKeyPrefix = "jrunmall:seckill";

        public String getGateway() {
            return gateway;
        }

        public void setGateway(String gateway) {
            this.gateway = gateway;
        }

        public String getContract() {
            return contract;
        }

        public void setContract(String contract) {
            this.contract = contract;
        }

        public String getEventStream() {
            return eventStream;
        }

        public void setEventStream(String eventStream) {
            this.eventStream = eventStream;
        }

        public String getObservability() {
            return observability;
        }

        public void setObservability(String observability) {
            this.observability = observability;
        }

        public String getSeckillStreamName() {
            return seckillStreamName;
        }

        public void setSeckillStreamName(String seckillStreamName) {
            this.seckillStreamName = seckillStreamName;
        }

        public String getSeckillConsumerGroup() {
            return seckillConsumerGroup;
        }

        public void setSeckillConsumerGroup(String seckillConsumerGroup) {
            this.seckillConsumerGroup = seckillConsumerGroup;
        }

        public String getSeckillConsumerName() {
            return seckillConsumerName;
        }

        public void setSeckillConsumerName(String seckillConsumerName) {
            this.seckillConsumerName = seckillConsumerName;
        }

        public String getSeckillKeyPrefix() {
            return seckillKeyPrefix;
        }

        public void setSeckillKeyPrefix(String seckillKeyPrefix) {
            this.seckillKeyPrefix = seckillKeyPrefix;
        }
    }
}





