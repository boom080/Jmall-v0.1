package com.shf.gulimall.product.app;

import com.shf.common.utils.R;
import com.shf.gulimall.product.app.dto.UserCartItemUpdateRequest;
import com.shf.gulimall.product.app.dto.UserCartItemUpsertRequest;
import com.shf.gulimall.product.app.dto.UserOrderCreateRequest;
import com.shf.gulimall.product.app.dto.UserOrderResponse;
import com.shf.gulimall.product.app.service.UserCommerceApplicationService;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("product/user")
public class UserCommerceController {

    private final UserCommerceApplicationService userCommerceApplicationService;

    public UserCommerceController(UserCommerceApplicationService userCommerceApplicationService) {
        this.userCommerceApplicationService = userCommerceApplicationService;
    }

    @GetMapping("/cart/items")
    public R getCartItems() {
        try {
            return R.ok().setData(userCommerceApplicationService.getCart());
        } catch (IllegalStateException ex) {
            return R.error(401, ex.getMessage());
        }
    }

    @PostMapping("/cart/items")
    public R addCartItem(@RequestBody UserCartItemUpsertRequest request) {
        try {
            return R.ok().setData(userCommerceApplicationService.addCartItem(request));
        } catch (IllegalStateException ex) {
            return R.error(401, ex.getMessage());
        } catch (IllegalArgumentException ex) {
            return R.error(400, ex.getMessage());
        }
    }

    @PutMapping("/cart/items/{skuId}")
    public R updateCartItem(@PathVariable("skuId") Long skuId, @RequestBody UserCartItemUpdateRequest request) {
        try {
            return R.ok().setData(userCommerceApplicationService.updateCartItem(skuId, request));
        } catch (IllegalStateException ex) {
            return R.error(401, ex.getMessage());
        } catch (IllegalArgumentException ex) {
            return R.error(400, ex.getMessage());
        }
    }

    @DeleteMapping("/cart/items/{skuId}")
    public R deleteCartItem(@PathVariable("skuId") Long skuId) {
        try {
            return R.ok().setData(userCommerceApplicationService.deleteCartItem(skuId));
        } catch (IllegalStateException ex) {
            return R.error(401, ex.getMessage());
        } catch (IllegalArgumentException ex) {
            return R.error(400, ex.getMessage());
        }
    }

    @PostMapping("/orders")
    public R createOrder(@RequestBody(required = false) UserOrderCreateRequest request) {
        try {
            UserOrderResponse response = userCommerceApplicationService.createOrder(request == null ? new UserOrderCreateRequest() : request);
            return R.ok().setData(response);
        } catch (IllegalStateException ex) {
            return R.error(401, ex.getMessage());
        } catch (IllegalArgumentException ex) {
            return R.error(400, ex.getMessage());
        }
    }

    @GetMapping("/orders")
    public R listOrders() {
        try {
            return R.ok().setData(userCommerceApplicationService.listOrders());
        } catch (IllegalStateException ex) {
            return R.error(401, ex.getMessage());
        }
    }

    @GetMapping("/orders/all")
    public R listAllOrders() {
        try {
            return R.ok().setData(userCommerceApplicationService.listAllOrders());
        } catch (IllegalStateException ex) {
            return R.error(401, ex.getMessage());
        }
    }

    @GetMapping("/orders/{orderId}")
    public R getOrder(@PathVariable("orderId") Long orderId) {
        try {
            UserOrderResponse response = userCommerceApplicationService.getOrder(orderId);
            if (response == null) {
                return R.error(404, "订单不存在");
            }
            return R.ok().setData(response);
        } catch (IllegalStateException ex) {
            return R.error(401, ex.getMessage());
        } catch (IllegalArgumentException ex) {
            return R.error(400, ex.getMessage());
        }
    }

    @GetMapping("/orders/all/{orderRef}")
    public R getOrderByRef(@PathVariable("orderRef") String orderRef) {
        try {
            UserOrderResponse response = userCommerceApplicationService.getOrderByRef(orderRef);
            if (response == null) {
                return R.error(404, "订单不存在");
            }
            return R.ok().setData(response);
        } catch (IllegalStateException ex) {
            return R.error(401, ex.getMessage());
        } catch (IllegalArgumentException ex) {
            return R.error(400, ex.getMessage());
        }
    }

    @PostMapping("/orders/{orderId}/pay")
    public R payOrder(@PathVariable("orderId") Long orderId) {
        try {
            return R.ok().setData(userCommerceApplicationService.payOrder(orderId));
        } catch (IllegalStateException ex) {
            return R.error(401, ex.getMessage());
        } catch (IllegalArgumentException ex) {
            return R.error(400, ex.getMessage());
        }
    }

    @PostMapping("/orders/{orderId}/address")
    public R confirmOrderAddress(@PathVariable("orderId") Long orderId, @RequestBody(required = false) UserOrderCreateRequest request) {
        try {
            return R.ok().setData(userCommerceApplicationService.confirmOrderAddress(
                    orderId,
                    request == null ? new UserOrderCreateRequest() : request
            ));
        } catch (IllegalStateException ex) {
            return R.error(401, ex.getMessage());
        } catch (IllegalArgumentException ex) {
            return R.error(400, ex.getMessage());
        }
    }

    @GetMapping("/seckill-orders")
    public R listCurrentUserSeckillOrders() {
        try {
            return R.ok().setData(userCommerceApplicationService.listCurrentUserSeckillOrders());
        } catch (IllegalStateException ex) {
            return R.error(401, ex.getMessage());
        }
    }
}





