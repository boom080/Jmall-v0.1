package com.shf.gulimall.product.app.dto;

import javax.validation.constraints.NotBlank;
import javax.validation.constraints.Size;

public class MerchantKnowledgeBaseDocumentTextRequest {

    @NotBlank(message = "文档标题不能为空")
    @Size(max = 120, message = "文档标题不能超过 120 个字符")
    private String title;

    @NotBlank(message = "文本文档内容不能为空")
    @Size(max = 8000, message = "文本文档内容不能超过 8000 个字符")
    private String content;

    public String getTitle() {
        return title;
    }

    public void setTitle(String title) {
        this.title = title;
    }

    public String getContent() {
        return content;
    }

    public void setContent(String content) {
        this.content = content;
    }
}





