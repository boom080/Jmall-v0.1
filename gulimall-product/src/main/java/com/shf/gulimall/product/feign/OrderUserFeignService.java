package com.shf.gulimall.product.feign;

import com.shf.common.utils.R;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;

@FeignClient("jrunmall-order")
public interface OrderUserFeignService {

    @GetMapping("/order/internal/seckill-orders/{userId}")
    R listUserSeckillOrders(@PathVariable("userId") Long userId);

    @GetMapping("/order/internal/seckill-orders/{userId}/{orderId}")
    R getUserSeckillOrderDetail(@PathVariable("userId") Long userId, @PathVariable("orderId") Long orderId);
}





