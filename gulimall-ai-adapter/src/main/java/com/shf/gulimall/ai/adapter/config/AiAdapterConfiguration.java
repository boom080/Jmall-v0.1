package com.shf.gulimall.ai.adapter.config;

import com.shf.gulimall.ai.adapter.client.AiHttpClient;
import com.shf.gulimall.ai.adapter.client.LangChain4jProductCopyClient;
import com.shf.gulimall.ai.adapter.service.ProductCopyAiService;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.client.RestTemplate;

import java.time.Duration;

@Configuration
@EnableConfigurationProperties(AiAdapterProperties.class)
public class AiAdapterConfiguration {

    @Bean
    public RestTemplate aiRestTemplate(RestTemplateBuilder builder, AiAdapterProperties properties) {
        return builder
                .setConnectTimeout(Duration.ofMillis(properties.getConnectTimeoutMs()))
                .setReadTimeout(Duration.ofMillis(properties.getReadTimeoutMs()))
                .build();
    }

    @Bean
    public AiHttpClient aiHttpClient(RestTemplate aiRestTemplate, AiAdapterProperties properties) {
        return new AiHttpClient(aiRestTemplate, properties);
    }

    @Bean
    public LangChain4jProductCopyClient langChain4jProductCopyClient(AiAdapterProperties properties) {
        return new LangChain4jProductCopyClient(properties);
    }

    @Bean
    public ProductCopyAiService productCopyAiService(AiHttpClient aiHttpClient, LangChain4jProductCopyClient langChain4jProductCopyClient) {
        return new ProductCopyAiService(aiHttpClient, langChain4jProductCopyClient);
    }
}





