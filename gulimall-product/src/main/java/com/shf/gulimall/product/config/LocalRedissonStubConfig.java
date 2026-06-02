package com.shf.gulimall.product.config;

import org.redisson.api.RedissonClient;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Profile;

import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;

@Configuration
@Profile("local")
@ConditionalOnProperty(name = "gulimall.redisson.enabled", havingValue = "false")
public class LocalRedissonStubConfig {

    @Bean
    public RedissonClient localRedissonStub() {
        InvocationHandler handler = new InvocationHandler() {
            @Override
            public Object invoke(Object proxy, Method method, Object[] args) {
                if (method.getDeclaringClass() == Object.class) {
                    switch (method.getName()) {
                        case "toString":
                            return "LocalRedissonStub";
                        case "hashCode":
                            return System.identityHashCode(proxy);
                        case "equals":
                            return proxy == args[0];
                        default:
                            return null;
                    }
                }
                throw new UnsupportedOperationException("Redisson is disabled under local profile.");
            }
        };
        return (RedissonClient) Proxy.newProxyInstance(
                RedissonClient.class.getClassLoader(),
                new Class<?>[]{RedissonClient.class},
                handler
        );
    }
}





