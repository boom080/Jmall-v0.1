package com.shf.gulimall.product.config;

import org.redisson.Redisson;
import org.redisson.api.RedissonClient;
import org.redisson.codec.JsonJacksonCodec;
import org.redisson.config.Config;
import org.redisson.config.SingleServerConfig;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.boot.autoconfigure.data.redis.RedisProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Lazy;
import org.springframework.context.annotation.Profile;
import org.springframework.util.StringUtils;

/**
 * @Description:
 * @Created: with IntelliJ IDEA.
 * @author: 夏沫止水
 * @createTime: 2020-06-11 09:39
 **/

@Configuration
@Profile("!local")
@ConditionalOnProperty(name = "gulimall.redisson.enabled", havingValue = "true", matchIfMissing = true)
public class MyRedissonConfig {

    private final RedisProperties redisProperties;

    public MyRedissonConfig(RedisProperties redisProperties) {
        this.redisProperties = redisProperties;
    }

    /**
     * 所有对Redisson的使用都是通过RedissonClient
     * @return
     */
    @Bean(destroyMethod="shutdown")
    @Lazy
    public RedissonClient redisson() {
        //1、创建配置
        Config config = new Config();
        config.setCodec(new JsonJacksonCodec());
        String scheme = redisProperties.isSsl() ? "rediss://" : "redis://";
        String address = scheme + redisProperties.getHost() + ":" + redisProperties.getPort();
        SingleServerConfig serverConfig = config.useSingleServer().setAddress(address);
        if (StringUtils.hasText(redisProperties.getPassword())) {
            serverConfig.setPassword(redisProperties.getPassword());
        }

        //2、根据Config创建出RedissonClient实例
        //Redis url should start with redis:// or rediss://
        return Redisson.create(config);
    }

}





