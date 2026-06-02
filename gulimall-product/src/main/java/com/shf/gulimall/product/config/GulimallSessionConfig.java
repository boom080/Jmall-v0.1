package com.shf.gulimall.product.config;

import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.redis.serializer.GenericJackson2JsonRedisSerializer;
import org.springframework.data.redis.serializer.RedisSerializer;
import org.springframework.session.data.redis.config.annotation.web.http.EnableRedisHttpSession;
import org.springframework.session.web.http.CookieSerializer;
import org.springframework.session.web.http.DefaultCookieSerializer;
import org.springframework.util.StringUtils;

@Configuration
@EnableRedisHttpSession
@ConditionalOnProperty(name = "gulimall.session.redis.enabled", havingValue = "true", matchIfMissing = true)
public class GulimallSessionConfig {

    private final SiteUrlProperties siteUrlProperties;

    public GulimallSessionConfig(SiteUrlProperties siteUrlProperties) {
        this.siteUrlProperties = siteUrlProperties;
    }

    @Bean
    public CookieSerializer cookieSerializer() {
        DefaultCookieSerializer cookieSerializer = new DefaultCookieSerializer();
        cookieSerializer.setCookieName("GULISESSION");
        if (StringUtils.hasText(siteUrlProperties.getCookieDomain())) {
            cookieSerializer.setDomainName(siteUrlProperties.getCookieDomain());
        }
        return cookieSerializer;
    }

    @Bean
    public RedisSerializer<Object> springSessionDefaultRedisSerializer() {
        return new GenericJackson2JsonRedisSerializer();
    }
}





