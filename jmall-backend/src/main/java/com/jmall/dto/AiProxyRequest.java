package com.jmall.dto;

import lombok.Data;

import java.util.Map;

@Data
public class AiProxyRequest {
    private String action;
    private Map<String, Object> params;
    private Map<String, Object> payload;
}
