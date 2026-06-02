package com.shf.gulimall.ai.adapter.client;

import org.junit.Test;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

import static org.junit.Assert.assertEquals;

public class LocalAiKeyResolverTests {

    @Test
    public void resolveReadsQuotedJrunmallKeyFromConfiguredEnvFile() throws Exception {
        String previous = System.getProperty("jrunmall.env.local");
        Path envFile = Files.createTempFile("jrunmall-ai", ".env.local");
        try {
            Files.write(envFile, (
                    "export JRUNMALL_AI_DEEPSEEK_API_KEY=\"sk-test-value\"\n" +
                    "DEEPSEEK_API_KEY=legacy-value\n"
            ).getBytes(StandardCharsets.UTF_8));
            System.setProperty("jrunmall.env.local", envFile.toString());

            String value = LocalAiKeyResolver.resolve("", "JRUNMALL_AI_DEEPSEEK_API_KEY", "DEEPSEEK_API_KEY");

            assertEquals("sk-test-value", value);
        } finally {
            if (previous == null) {
                System.clearProperty("jrunmall.env.local");
            } else {
                System.setProperty("jrunmall.env.local", previous);
            }
            Files.deleteIfExists(envFile);
        }
    }

    @Test
    public void resolveKeepsExplicitConfiguredValueFirst() {
        String value = LocalAiKeyResolver.resolve(" configured-key ", "JRUNMALL_AI_DEEPSEEK_API_KEY");

        assertEquals("configured-key", value);
    }

    @Test
    public void resolveAcceptsDashscopeAliasForQwen() throws Exception {
        String previous = System.getProperty("jrunmall.env.local");
        Path envFile = Files.createTempFile("jrunmall-ai-qwen", ".env.local");
        try {
            Files.write(envFile, "DASHSCOPE_API_KEY=sk-qwen-value\n".getBytes(StandardCharsets.UTF_8));
            System.setProperty("jrunmall.env.local", envFile.toString());

            String value = LocalAiKeyResolver.resolve("", "JRUNMALL_AI_QWEN_API_KEY", "QWEN_API_KEY", "DASHSCOPE_API_KEY");

            assertEquals("sk-qwen-value", value);
        } finally {
            if (previous == null) {
                System.clearProperty("jrunmall.env.local");
            } else {
                System.setProperty("jrunmall.env.local", previous);
            }
            Files.deleteIfExists(envFile);
        }
    }
}
