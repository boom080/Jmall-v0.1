package com.shf.gulimall.product.app;

import com.shf.common.utils.R;
import com.shf.gulimall.product.app.service.UserCommerceApplicationService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("product/merchant")
public class MerchantOrderController {

    private final UserCommerceApplicationService userCommerceApplicationService;

    public MerchantOrderController(UserCommerceApplicationService userCommerceApplicationService) {
        this.userCommerceApplicationService = userCommerceApplicationService;
    }

    @GetMapping("/orders")
    public R listOrders() {
        return R.ok().setData(userCommerceApplicationService.listMerchantOrders());
    }
}





