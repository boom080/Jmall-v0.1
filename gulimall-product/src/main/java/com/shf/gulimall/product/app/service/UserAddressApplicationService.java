package com.shf.gulimall.product.app.service;

import com.shf.common.utils.R;
import com.shf.gulimall.product.app.dto.CurrentUserProfile;
import com.shf.gulimall.product.app.dto.UserAddressRequest;
import com.shf.gulimall.product.app.dto.UserAddressResponse;
import com.shf.gulimall.product.feign.MemberUserFeignService;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;
import java.util.Map;

@Service
public class UserAddressApplicationService {

    private final MemberUserFeignService memberUserFeignService;
    private final CurrentUserResolver currentUserResolver;

    public UserAddressApplicationService(MemberUserFeignService memberUserFeignService,
                                         CurrentUserResolver currentUserResolver) {
        this.memberUserFeignService = memberUserFeignService;
        this.currentUserResolver = currentUserResolver;
    }

    public List<UserAddressResponse> listCurrentUserAddresses() {
        CurrentUserProfile user = currentUserResolver.requireCurrentUser();
        List<UserAddressResponse> result = memberUserFeignService.listAddresses(user.getUserId());
        if (result == null) {
            return Collections.emptyList();
        }
        result.sort(Comparator.comparing(UserAddressResponse::getDefaultStatus, Comparator.nullsLast(Comparator.reverseOrder()))
                .thenComparing(UserAddressResponse::getId, Comparator.nullsLast(Comparator.naturalOrder())));
        return result;
    }

    public UserAddressResponse createAddress(UserAddressRequest request) {
        CurrentUserProfile user = currentUserResolver.requireCurrentUser();
        validate(request);
        UserAddressResponse payload = toPayload(request, user.getUserId());
        if (payload.getDefaultStatus() == null) {
            payload.setDefaultStatus(0);
        }
        if (payload.getDefaultStatus() == 1) {
            clearDefaultAddress(user.getUserId(), null);
        }
        R response = memberUserFeignService.saveAddress(payload);
        if (response.get("code") instanceof Number && ((Number) response.get("code")).intValue() != 0) {
            throw new IllegalArgumentException(String.valueOf(response.get("msg")));
        }
        return findLatestAddress(user.getUserId(), payload.getName(), payload.getPhone(), payload.getDetailAddress());
    }

    public UserAddressResponse updateAddress(Long addressId, UserAddressRequest request) {
        CurrentUserProfile user = currentUserResolver.requireCurrentUser();
        validate(request);
        UserAddressResponse existing = getOwnedAddress(addressId, user.getUserId());
        UserAddressResponse payload = toPayload(request, user.getUserId());
        payload.setId(existing.getId());
        if (payload.getDefaultStatus() != null && payload.getDefaultStatus() == 1) {
            clearDefaultAddress(user.getUserId(), addressId);
        }
        R response = memberUserFeignService.updateAddress(payload);
        if (response.get("code") instanceof Number && ((Number) response.get("code")).intValue() != 0) {
            throw new IllegalArgumentException(String.valueOf(response.get("msg")));
        }
        return getOwnedAddress(addressId, user.getUserId());
    }

    public void deleteAddress(Long addressId) {
        CurrentUserProfile user = currentUserResolver.requireCurrentUser();
        UserAddressResponse existing = getOwnedAddress(addressId, user.getUserId());
        memberUserFeignService.deleteAddress(new Long[]{existing.getId()});
    }

    public UserAddressResponse getAddressForCurrentUser(Long addressId) {
        CurrentUserProfile user = currentUserResolver.requireCurrentUser();
        return getOwnedAddress(addressId, user.getUserId());
    }

    private UserAddressResponse toPayload(UserAddressRequest request, Long userId) {
        UserAddressResponse payload = new UserAddressResponse();
        payload.setId(request.getId());
        payload.setMemberId(userId);
        payload.setName(trim(request.getName()));
        payload.setPhone(trim(request.getPhone()));
        payload.setProvince(trim(request.getProvince()));
        payload.setCity(trim(request.getCity()));
        payload.setRegion(trim(request.getRegion()));
        payload.setDetailAddress(trim(request.getDetailAddress()));
        payload.setDefaultStatus(request.getDefaultStatus());
        return payload;
    }

    private UserAddressResponse getOwnedAddress(Long addressId, Long userId) {
        R response = memberUserFeignService.addressInfo(addressId);
        Object raw = response.get("memberReceiveAddress");
        if (!(raw instanceof Map)) {
            throw new IllegalArgumentException("地址不存在");
        }
        UserAddressResponse address = map((Map<?, ?>) raw);
        if (address.getMemberId() == null || !address.getMemberId().equals(userId)) {
            throw new IllegalArgumentException("地址不存在");
        }
        return address;
    }

    private UserAddressResponse map(Map<?, ?> raw) {
        UserAddressResponse address = new UserAddressResponse();
        address.setId(raw.get("id") == null ? null : Long.valueOf(String.valueOf(raw.get("id"))));
        address.setMemberId(raw.get("memberId") == null ? null : Long.valueOf(String.valueOf(raw.get("memberId"))));
        address.setName(raw.get("name") == null ? "" : String.valueOf(raw.get("name")));
        address.setPhone(raw.get("phone") == null ? "" : String.valueOf(raw.get("phone")));
        address.setProvince(raw.get("province") == null ? "" : String.valueOf(raw.get("province")));
        address.setCity(raw.get("city") == null ? "" : String.valueOf(raw.get("city")));
        address.setRegion(raw.get("region") == null ? "" : String.valueOf(raw.get("region")));
        address.setDetailAddress(raw.get("detailAddress") == null ? "" : String.valueOf(raw.get("detailAddress")));
        address.setDefaultStatus(raw.get("defaultStatus") == null ? 0 : Integer.valueOf(String.valueOf(raw.get("defaultStatus"))));
        return address;
    }

    private void clearDefaultAddress(Long userId, Long preserveId) {
        List<UserAddressResponse> addresses = memberUserFeignService.listAddresses(userId);
        if (addresses == null || addresses.isEmpty()) {
            return;
        }
        for (UserAddressResponse address : new ArrayList<UserAddressResponse>(addresses)) {
            if (address.getDefaultStatus() != null && address.getDefaultStatus() == 1) {
                if (preserveId != null && preserveId.equals(address.getId())) {
                    continue;
                }
                address.setDefaultStatus(0);
                memberUserFeignService.updateAddress(address);
            }
        }
    }

    private UserAddressResponse findLatestAddress(Long userId, String name, String phone, String detailAddress) {
        List<UserAddressResponse> addresses = memberUserFeignService.listAddresses(userId);
        if (addresses == null || addresses.isEmpty()) {
            throw new IllegalArgumentException("地址保存成功，但读取失败");
        }
        UserAddressResponse matched = null;
        for (UserAddressResponse address : addresses) {
            if (name.equals(address.getName()) && phone.equals(address.getPhone()) && detailAddress.equals(address.getDetailAddress())) {
                if (matched == null || (address.getId() != null && address.getId() > matched.getId())) {
                    matched = address;
                }
            }
        }
        return matched == null ? addresses.get(0) : matched;
    }

    private void validate(UserAddressRequest request) {
        if (request == null) {
            throw new IllegalArgumentException("地址请求不能为空");
        }
        if (trim(request.getName()).isEmpty()) {
            throw new IllegalArgumentException("收件人不能为空");
        }
        if (trim(request.getPhone()).isEmpty()) {
            throw new IllegalArgumentException("手机号不能为空");
        }
        if (trim(request.getDetailAddress()).isEmpty()) {
            throw new IllegalArgumentException("详细地址不能为空");
        }
    }

    private String trim(String value) {
        return value == null ? "" : value.trim();
    }
}





