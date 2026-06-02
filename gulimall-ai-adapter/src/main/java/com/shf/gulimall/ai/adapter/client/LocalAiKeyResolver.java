package com.shf.gulimall.ai.adapter.client;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;

class LocalAiKeyResolver {

    private LocalAiKeyResolver() {
    }

    static String resolve(String configuredValue, String... names) {
        if (hasText(configuredValue)) {
            return stripQuotes(configuredValue.trim());
        }
        if (names == null) {
            return "";
        }
        for (String name : names) {
            String value = readSystemValue(name);
            if (hasText(value)) {
                return stripQuotes(value.trim());
            }
        }
        for (Path envFile : candidateEnvFiles()) {
            String value = readEnvFileValue(envFile, names);
            if (hasText(value)) {
                return stripQuotes(value.trim());
            }
        }
        return "";
    }

    private static String readSystemValue(String name) {
        if (!hasText(name)) {
            return "";
        }
        String property = System.getProperty(name);
        if (hasText(property)) {
            return property;
        }
        return System.getenv(name);
    }

    private static Set<Path> candidateEnvFiles() {
        Set<Path> files = new LinkedHashSet<>();
        addEnvFile(files, System.getProperty("jrunmall.env.local"));
        addEnvFile(files, System.getenv("JRUNMALL_ENV_FILE"));

        Path current = Paths.get("").toAbsolutePath();
        for (int i = 0; i < 6 && current != null; i++) {
            files.add(current.resolve(".env.local"));
            files.add(current.resolve(".env"));
            current = current.getParent();
        }
        return files;
    }

    private static void addEnvFile(Set<Path> files, String value) {
        if (hasText(value)) {
            files.add(Paths.get(value.trim()).toAbsolutePath());
        }
    }

    private static String readEnvFileValue(Path envFile, String... names) {
        if (envFile == null || !Files.isRegularFile(envFile)) {
            return "";
        }
        try {
            List<String> lines = Files.readAllLines(envFile, StandardCharsets.UTF_8);
            for (String line : lines) {
                EnvEntry entry = parseLine(line);
                if (entry == null || !hasText(entry.value)) {
                    continue;
                }
                for (String name : names) {
                    if (entry.name.equals(name)) {
                        return entry.value;
                    }
                }
            }
        } catch (IOException ignored) {
            return "";
        }
        return "";
    }

    private static EnvEntry parseLine(String line) {
        if (line == null) {
            return null;
        }
        String normalized = stripBom(line).trim();
        if (normalized.isEmpty() || normalized.startsWith("#")) {
            return null;
        }
        if (normalized.startsWith("export ")) {
            normalized = normalized.substring("export ".length()).trim();
        }
        int equals = normalized.indexOf('=');
        if (equals <= 0) {
            return null;
        }
        String name = normalized.substring(0, equals).trim();
        String value = stripInlineComment(normalized.substring(equals + 1).trim());
        return hasText(name) ? new EnvEntry(name, stripQuotes(value)) : null;
    }

    private static String stripInlineComment(String value) {
        if (!hasText(value) || value.startsWith("\"") || value.startsWith("'")) {
            return value;
        }
        int comment = value.indexOf(" #");
        return comment >= 0 ? value.substring(0, comment).trim() : value;
    }

    private static String stripQuotes(String value) {
        if (value == null || value.length() < 2) {
            return value == null ? "" : value;
        }
        String trimmed = value.trim();
        if ((trimmed.startsWith("\"") && trimmed.endsWith("\"")) || (trimmed.startsWith("'") && trimmed.endsWith("'"))) {
            return trimmed.substring(1, trimmed.length() - 1).trim();
        }
        return trimmed;
    }

    private static String stripBom(String value) {
        return value != null && value.startsWith("\uFEFF") ? value.substring(1) : value;
    }

    private static boolean hasText(String value) {
        return value != null && !value.trim().isEmpty();
    }

    private static class EnvEntry {
        private final String name;
        private final String value;

        private EnvEntry(String name, String value) {
            this.name = name;
            this.value = value;
        }
    }
}
