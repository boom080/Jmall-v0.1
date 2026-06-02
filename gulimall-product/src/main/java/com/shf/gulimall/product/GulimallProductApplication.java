package com.shf.gulimall.product;

import com.shf.gulimall.ai.adapter.config.AiAdapterConfiguration;
import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cache.annotation.EnableCaching;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.cloud.openfeign.EnableFeignClients;
import org.springframework.context.annotation.Import;

@EnableCaching
@EnableFeignClients(basePackages = "com.shf.gulimall.product.feign")
@EnableDiscoveryClient
@MapperScan("com.shf.gulimall.product.dao")
@Import(AiAdapterConfiguration.class)
@SpringBootApplication
public class GulimallProductApplication {

    public static void main(String[] args) {
        SpringApplication.run(GulimallProductApplication.class, args);
    }
}





