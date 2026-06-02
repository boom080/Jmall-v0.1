package com.shf.gulimall.product.app;

import com.shf.common.utils.R;
import com.shf.gulimall.product.app.dto.MerchantKnowledgeBaseCreateRequest;
import com.shf.gulimall.product.app.dto.MerchantKnowledgeBaseDocumentResponse;
import com.shf.gulimall.product.app.dto.MerchantKnowledgeBaseDocumentTextRequest;
import com.shf.gulimall.product.app.dto.ProductAiKnowledgeBaseOptionResponse;
import com.shf.gulimall.product.app.service.ProductAiApplicationService;
import org.springframework.http.MediaType;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import javax.validation.Valid;
import java.io.IOException;
import java.util.List;


@Validated
@RestController
@RequestMapping("product/merchant/knowledge-bases")
public class MerchantKnowledgeBaseController {

    private final ProductAiApplicationService productAiApplicationService;

    public MerchantKnowledgeBaseController(ProductAiApplicationService productAiApplicationService) {
        this.productAiApplicationService = productAiApplicationService;
    }

    @GetMapping
    public R listKnowledgeBases() {
        List<ProductAiKnowledgeBaseOptionResponse> knowledgeBases = productAiApplicationService.listMerchantKnowledgeBases();
        return R.ok().setData(knowledgeBases);
    }

    @PostMapping
    public R createKnowledgeBase(@Valid @RequestBody MerchantKnowledgeBaseCreateRequest request) {
        try {
            return R.ok().setData(
                    productAiApplicationService.createMerchantKnowledgeBase(request.getName(), request.getDescription())
            );
        } catch (RuntimeException ex) {
            return R.error(502, "知识库创建失败：" + ex.getMessage());
        }
    }

    @GetMapping("/{knowledgeBaseId}/documents")
    public R listDocuments(@PathVariable("knowledgeBaseId") String knowledgeBaseId) {
        List<MerchantKnowledgeBaseDocumentResponse> documents =
                productAiApplicationService.listMerchantKnowledgeBaseDocuments(knowledgeBaseId);
        return R.ok().setData(documents);
    }

    @PostMapping("/{knowledgeBaseId}/documents/text")
    public R importTextDocument(
            @PathVariable("knowledgeBaseId") String knowledgeBaseId,
            @Valid @RequestBody MerchantKnowledgeBaseDocumentTextRequest request
    ) {
        try {
            return R.ok().setData(
                    productAiApplicationService.importMerchantKnowledgeBaseTextDocument(
                            knowledgeBaseId,
                            request.getTitle(),
                            request.getContent()
                    )
            );
        } catch (RuntimeException ex) {
            return R.error(502, "文本导入失败：" + ex.getMessage());
        }
    }

    @PostMapping(value = "/{knowledgeBaseId}/documents/pdf", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public R importPdfDocument(
            @PathVariable("knowledgeBaseId") String knowledgeBaseId,
            @RequestParam(value = "title", required = false) String title,
            @RequestParam("file") MultipartFile file
    ) {
        try {
            return R.ok().setData(
                    productAiApplicationService.importMerchantKnowledgeBasePdfDocument(
                            knowledgeBaseId,
                            title,
                            file.getOriginalFilename(),
                            file.getBytes()
                    )
            );
        } catch (IllegalArgumentException ex) {
            return R.error(400, ex.getMessage());
        } catch (IOException ex) {
            return R.error(400, "PDF 文件读取失败：" + ex.getMessage());
        } catch (RuntimeException ex) {
            return R.error(502, "PDF 导入失败：" + ex.getMessage());
        }
    }
}





