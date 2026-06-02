package com.shf.gulimall.product.app.dto;

import javax.validation.constraints.NotBlank;
import javax.validation.constraints.Size;

public class MerchantKnowledgeBaseCreateRequest {

    @NotBlank(message = "知识库名称不能为空")
    @Size(max = 80, message = "知识库名称不能超过 80 个字符")
    private String name;

    @Size(max = 240, message = "知识库说明不能超过 240 个字符")
    private String description;

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }
}





