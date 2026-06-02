package com.shf.gulimall.product.app;

import com.shf.common.utils.R;
import com.shf.gulimall.product.app.dto.UserAddressRequest;
import com.shf.gulimall.product.app.service.UserAddressApplicationService;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("user/addresses")
public class UserAddressController {

    private final UserAddressApplicationService userAddressApplicationService;

    public UserAddressController(UserAddressApplicationService userAddressApplicationService) {
        this.userAddressApplicationService = userAddressApplicationService;
    }

    @GetMapping
    public R list() {
        try {
            return R.ok().setData(userAddressApplicationService.listCurrentUserAddresses());
        } catch (IllegalStateException ex) {
            return R.error(401, ex.getMessage());
        }
    }

    @PostMapping
    public R create(@RequestBody UserAddressRequest request) {
        try {
            return R.ok().setData(userAddressApplicationService.createAddress(request));
        } catch (IllegalStateException ex) {
            return R.error(401, ex.getMessage());
        } catch (IllegalArgumentException ex) {
            return R.error(400, ex.getMessage());
        }
    }

    @PutMapping("/{addressId}")
    public R update(@PathVariable("addressId") Long addressId, @RequestBody UserAddressRequest request) {
        try {
            return R.ok().setData(userAddressApplicationService.updateAddress(addressId, request));
        } catch (IllegalStateException ex) {
            return R.error(401, ex.getMessage());
        } catch (IllegalArgumentException ex) {
            return R.error(400, ex.getMessage());
        }
    }

    @DeleteMapping("/{addressId}")
    public R delete(@PathVariable("addressId") Long addressId) {
        try {
            userAddressApplicationService.deleteAddress(addressId);
            return R.ok();
        } catch (IllegalStateException ex) {
            return R.error(401, ex.getMessage());
        } catch (IllegalArgumentException ex) {
            return R.error(400, ex.getMessage());
        }
    }
}





