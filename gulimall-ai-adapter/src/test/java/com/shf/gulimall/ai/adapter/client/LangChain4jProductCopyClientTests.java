package com.shf.gulimall.ai.adapter.client;

import com.shf.gulimall.ai.adapter.config.AiAdapterProperties;
import com.shf.gulimall.ai.adapter.model.AiModelOption;
import com.shf.gulimall.ai.adapter.model.ProductCopyAiRequest;
import org.junit.Test;

import java.util.List;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

public class LangChain4jProductCopyClientTests {

    @Test
    public void getModelOptionsPlacesConfiguredDeepseekModelFirst() {
        AiAdapterProperties properties = new AiAdapterProperties();
        properties.setDeepseekApiKey("sk-deepseek");
        properties.setDeepseekModels("deepseek-chat");

        LangChain4jProductCopyClient client = new LangChain4jProductCopyClient(properties);

        List<AiModelOption> options = client.getModelOptions();

        assertFalse(options.isEmpty());
        assertEquals("langchain4j-openai:deepseek-chat", options.get(0).getId());
        assertEquals("DeepSeek / deepseek-chat", options.get(0).getLabel());
    }

    @Test
    public void supportsLegacyProviderNamesFromAiServicesCatalog() {
        AiAdapterProperties properties = new AiAdapterProperties();
        LangChain4jProductCopyClient client = new LangChain4jProductCopyClient(properties);

        ProductCopyAiRequest deepseekRequest = new ProductCopyAiRequest();
        deepseekRequest.setModelProvider("deepseek");
        ProductCopyAiRequest qwenRequest = new ProductCopyAiRequest();
        qwenRequest.setModelProvider("qwen");

        assertTrue(client.supports(deepseekRequest));
        assertTrue(client.supports(qwenRequest));
    }
}
