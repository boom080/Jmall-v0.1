package com.shf.gulimall.product.feign;

import com.shf.common.utils.R;
import com.shf.gulimall.product.app.dto.UserAddressResponse;
import com.shf.gulimall.product.app.dto.UserAuthLoginRequest;
import com.shf.gulimall.product.app.dto.UserAuthRegisterRequest;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@FeignClient("jrunmall-member")
public interface MemberUserFeignService {

    @PostMapping("/member/member/register")
    R register(@RequestBody UserAuthRegisterRequest request);

    @PostMapping("/member/member/login")
    R login(@RequestBody UserAuthLoginRequest request);

    @GetMapping("/member/memberreceiveaddress/{memberId}/address")
    List<UserAddressResponse> listAddresses(@PathVariable("memberId") Long memberId);

    @GetMapping("/member/memberreceiveaddress/info/{id}")
    R addressInfo(@PathVariable("id") Long id);

    @PostMapping("/member/memberreceiveaddress/save")
    R saveAddress(@RequestBody UserAddressResponse request);

    @PostMapping("/member/memberreceiveaddress/update")
    R updateAddress(@RequestBody UserAddressResponse request);

    @PostMapping("/member/memberreceiveaddress/delete")
    R deleteAddress(@RequestBody Long[] ids);
}





