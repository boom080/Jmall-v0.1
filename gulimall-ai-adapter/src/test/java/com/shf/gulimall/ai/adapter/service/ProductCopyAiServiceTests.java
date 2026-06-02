package com.shf.gulimall.ai.adapter.service;

import com.shf.gulimall.ai.adapter.client.AiHttpClient;
import com.shf.gulimall.ai.adapter.client.LangChain4jProductCopyClient;
import com.shf.gulimall.ai.adapter.config.AiAdapterProperties;
import com.shf.gulimall.ai.adapter.model.AiModelOption;
import org.junit.Test;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.web.client.RestTemplate;

import java.util.List;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.method;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess;

public class ProductCopyAiServiceTests {

    @Test
    public void getAvailableModelsUsesPythonAiServicesCatalog() {
        RestTemplate restTemplate = new RestTemplate();
        MockRestServiceServer server = MockRestServiceServer.bindTo(restTemplate).build();

        AiAdapterProperties properties = new AiAdapterProperties();
        properties.setBaseUrl("http://127.0.0.1:18080");
        properties.setModelsPath("/api/models");
        properties.setDeepseekApiKey("sk-deepseek");
        properties.setDeepseekModel("deepseek-chat");
        properties.setQwenApiKey("sk-qwen");
        properties.setQwenModel("qwen3-max");

        server.expect(requestTo("http://127.0.0.1:18080/api/models"))
                .andExpect(method(HttpMethod.GET))
                .andRespond(withSuccess(
                        "[" +
                                "{\"id\":\"mock:mock-product-copy-v1\",\"label\":\"Mock / mock-product-copy-v1\",\"provider\":\"mock\",\"modelName\":\"mock-product-copy-v1\"}," +
                                "{\"id\":\"deepseek:deepseek-chat\",\"label\":\"DeepSeek / deepseek-chat\",\"provider\":\"deepseek\",\"modelName\":\"deepseek-chat\"}," +
                                "{\"id\":\"qwen:qwen3-max\",\"label\":\"Qwen / qwen3-max\",\"provider\":\"qwen\",\"modelName\":\"qwen3-max\"}" +
                                "]",
                        MediaType.APPLICATION_JSON
                ));

        ProductCopyAiService service = new ProductCopyAiService(
                new AiHttpClient(restTemplate, properties),
                new LangChain4jProductCopyClient(properties)
        );

        List<AiModelOption> models = service.getAvailableModels();

        assertTrue(containsId(models, "mock:mock-product-copy-v1"));
        assertTrue(containsId(models, "deepseek:deepseek-chat"));
        assertTrue(containsId(models, "qwen:qwen3-max"));
        assertFalse(containsId(models, "langchain4j-openai:deepseek-chat"));
        assertFalse(containsId(models, "langchain4j-openai:qwen3-max"));
        server.verify();
    }

    private boolean containsId(List<AiModelOption> models, String id) {
        for (AiModelOption model : models) {
            if (id.equals(model.getId())) {
                return true;
            }
        }
        return false;
    }
}
