package com.shf.gulimall.product.app;

import com.shf.common.utils.R;
import com.shf.gulimall.product.app.dto.UserCatalogProductDetailResponse;
import com.shf.gulimall.product.app.dto.UserCatalogProductPageResponse;
import com.shf.gulimall.product.app.service.UserCatalogApplicationService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;
import java.util.concurrent.ExecutionException;

@RestController
@RequestMapping("product/user/catalog")
public class UserCatalogController {

    private final UserCatalogApplicationService userCatalogApplicationService;

    public UserCatalogController(UserCatalogApplicationService userCatalogApplicationService) {
        this.userCatalogApplicationService = userCatalogApplicationService;
    }

    @GetMapping("/products")
    public R listProducts(@RequestParam Map<String, Object> params) {
        UserCatalogProductPageResponse response = userCatalogApplicationService.listProducts(params);
        return R.ok().setData(response);
    }

    @GetMapping("/products/{skuId}")
    public R productDetail(@PathVariable("skuId") Long skuId) throws ExecutionException, InterruptedException {
        UserCatalogProductDetailResponse response = userCatalogApplicationService.getProductDetail(skuId);
        if (response == null) {
            return R.error(404, "商品不存在");
        }
        return R.ok().setData(response);
    }
}





