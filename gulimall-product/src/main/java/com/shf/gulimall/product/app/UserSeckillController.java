package com.shf.gulimall.product.app;

import com.shf.common.utils.R;
import com.shf.gulimall.product.app.dto.SeckillSubmitRequest;
import com.shf.gulimall.product.app.service.UserSeckillApplicationService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("product/user/seckill")
public class UserSeckillController {

    private final UserSeckillApplicationService userSeckillApplicationService;

    public UserSeckillController(UserSeckillApplicationService userSeckillApplicationService) {
        this.userSeckillApplicationService = userSeckillApplicationService;
    }

    @GetMapping("/current")
    public R currentDeal() {
        try {
            return R.ok().setData(userSeckillApplicationService.currentDeal());
        } catch (IllegalArgumentException ex) {
            return R.error(400, ex.getMessage());
        }
    }

    @PostMapping("/submit")
    public R submit(@RequestBody(required = false) SeckillSubmitRequest request) {
        try {
            return R.ok().setData(userSeckillApplicationService.submit(request == null ? new SeckillSubmitRequest() : request));
        } catch (IllegalStateException ex) {
            return R.error(401, ex.getMessage());
        } catch (IllegalArgumentException ex) {
            return R.error(400, ex.getMessage());
        } catch (Exception ex) {
            return R.error(503, "秒杀服务暂时不可用：" + ex.getMessage());
        }
    }

    @PostMapping("/consume-once")
    public R consumeOnce() {
        return R.error(410, "秒杀 Streams 消费已迁移到 jrunmall-order，请调用 /order/seckill/streams/consume-once");
    }
}





