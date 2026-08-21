package com.jmall.common;

import lombok.Data;
import org.springframework.http.HttpStatus;

import java.util.HashMap;
import java.util.Map;

@Data
public class R {

    private int code;
    private String msg;
    private Object data;

    private R() {
    }

    public static R ok() {
        R r = new R();
        r.code = BizCodeEnum.SUCCESS.getCode();
        r.msg = BizCodeEnum.SUCCESS.getMsg();
        r.data = new HashMap<>();
        return r;
    }

    public static R ok(Object data) {
        R r = new R();
        r.code = BizCodeEnum.SUCCESS.getCode();
        r.msg = BizCodeEnum.SUCCESS.getMsg();
        r.data = data;
        return r;
    }

    public static R ok(String msg, Object data) {
        R r = new R();
        r.code = BizCodeEnum.SUCCESS.getCode();
        r.msg = msg;
        r.data = data;
        return r;
    }

    public static R error(int code, String msg) {
        R r = new R();
        r.code = code;
        r.msg = msg;
        r.data = new HashMap<>();
        return r;
    }

    public static R error(BizCodeEnum bizCode) {
        R r = new R();
        r.code = bizCode.getCode();
        r.msg = bizCode.getMsg();
        r.data = new HashMap<>();
        return r;
    }

    public static R error(int code, String msg, Object data) {
        R r = new R();
        r.code = code;
        r.msg = msg;
        r.data = data;
        return r;
    }

    public static R error(HttpStatus status, String msg) {
        R r = new R();
        r.code = status.value();
        r.msg = msg;
        r.data = new HashMap<>();
        return r;
    }

    @SuppressWarnings("unchecked")
    public <T> T getData(Class<T> clazz) {
        return (T) data;
    }
}
