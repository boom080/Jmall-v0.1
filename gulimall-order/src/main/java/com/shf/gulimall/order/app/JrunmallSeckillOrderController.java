package com.shf.gulimall.order.app;

import com.shf.common.utils.R;
import com.shf.gulimall.order.app.service.JrunmallSeckillOrderService;
import com.shf.gulimall.order.app.service.JrunmallSeckillStreamConsumerService;
import com.shf.gulimall.order.config.JrunmallSeckillProperties;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("order")
public class JrunmallSeckillOrderController {

    private final JrunmallSeckillStreamConsumerService streamConsumerService;
    private final JrunmallSeckillOrderService orderService;
    private final JrunmallSeckillProperties properties;

    public JrunmallSeckillOrderController(JrunmallSeckillStreamConsumerService streamConsumerService,
                                          JrunmallSeckillOrderService orderService,
                                          JrunmallSeckillProperties properties) {
        this.streamConsumerService = streamConsumerService;
        this.orderService = orderService;
        this.properties = properties;
    }

    @PostMapping("/seckill/streams/consume-once")
    public R consumeOnce() {
        return R.ok().put("consumed", streamConsumerService.consumeOnce());
    }

    @PostMapping("/seckill/streams/retry-pending")
    public R retryPending() {
        return R.ok().put("processed", streamConsumerService.retryPendingOnce());
    }

    @GetMapping("/merchant/seckill-orders")
    public R listMerchantSeckillOrders() {
        return R.ok().setData(orderService.listMerchantSeckillOrders());
    }

    @GetMapping("/user/seckill-orders")
    public R listUserSeckillOrders() {
        return R.ok().setData(orderService.listUserSeckillOrders(properties.getDemoUserId()));
    }

    @GetMapping("/internal/seckill-orders/{userId}")
    public R listInternalUserSeckillOrders(@PathVariable("userId") Long userId) {
        return R.ok().setData(orderService.listUserSeckillOrders(userId));
    }

    @GetMapping("/internal/seckill-orders/{userId}/{orderId}")
    public R getInternalUserSeckillOrderDetail(@PathVariable("userId") Long userId,
                                               @PathVariable("orderId") Long orderId) {
        Object detail = orderService.getUserSeckillOrderDetail(userId, orderId);
        if (detail == null) {
            return R.error(404, "秒杀订单不存在");
        }
        return R.ok().setData(detail);
    }
}





