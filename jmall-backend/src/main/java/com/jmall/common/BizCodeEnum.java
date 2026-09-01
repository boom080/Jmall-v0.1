package com.jmall.common;

import lombok.Getter;

@Getter
public enum BizCodeEnum {

    SUCCESS(10000, "success"),
    PARAM_ERROR(10001, "parameter error"),
    AUTH_ERROR(10010, "authentication error"),
    INSUFFICIENT_GOLD(10020, "insufficient gold balance"),
    PRODUCT_NOT_FOUND(10030, "product not found"),
    PRODUCT_NOT_PUBLISHABLE(10034, "product is not publishable"),
    STORE_NOT_FOUND(10040, "store not found"),
    USER_NOT_FOUND(10050, "user not found"),
    DUPLICATE_USERNAME(10060, "username already exists"),
    INVALID_CREDENTIALS(10070, "invalid username or password"),
    ALREADY_CHECKED_IN(10080, "already checked in today"),
    OPERATION_FAILED(10090, "operation failed"),
    INTERNAL_ERROR(50000, "internal server error");

    private final int code;
    private final String msg;

    BizCodeEnum(int code, String msg) {
        this.code = code;
        this.msg = msg;
    }
}
