package com.shf.gulimall.product.app;

import com.shf.common.utils.R;
import com.shf.gulimall.product.app.dto.ProductAiKnowledgeBaseOptionResponse;
import com.shf.gulimall.product.app.dto.ProductAiModelOptionResponse;
import com.shf.gulimall.product.app.service.ProductAiApplicationService;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.List;


@RestController
@RequestMapping("product/ai")
public class ProductAiCatalogController {

    private final ProductAiApplicationService productAiApplicationService;

    public ProductAiCatalogController(ProductAiApplicationService productAiApplicationService) {
        this.productAiApplicationService = productAiApplicationService;
    }

    @GetMapping("/models")
    public R listModels() {
        List<ProductAiModelOptionResponse> models = productAiApplicationService.listAvailableModels();
        return R.ok().setData(models);
    }

    @GetMapping("/knowledge-bases")
    public R listKnowledgeBases() {
        List<ProductAiKnowledgeBaseOptionResponse> knowledgeBases = productAiApplicationService.listKnowledgeBases();
        return R.ok().setData(knowledgeBases);
    }

    @PostMapping(value = "/knowledge-bases/upload-txt", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public R uploadTxtKnowledgeBase(
            @RequestParam("name") String name,
            @RequestParam(value = "description", required = false) String description,
            @RequestParam("file") MultipartFile file
    ) {
        try {
            return R.ok().setData(
                    productAiApplicationService.uploadTxtKnowledgeBase(
                            name,
                            description,
                            file.getOriginalFilename(),
                            file.getBytes()
                    )
            );
        } catch (IllegalArgumentException ex) {
            return R.error(400, ex.getMessage());
        } catch (IOException ex) {
            return R.error(400, "txt 文件读取失败：" + ex.getMessage());
        } catch (RuntimeException ex) {
            return R.error(502, "txt 上传创建知识库失败：" + ex.getMessage());
        }
    }
}





