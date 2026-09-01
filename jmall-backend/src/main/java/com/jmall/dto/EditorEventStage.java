package com.jmall.dto;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonValue;

/**
 * The small, fixed vocabulary accepted by the editor telemetry endpoint.
 */
public enum EditorEventStage {
    EDITOR_OPENED("editor_opened"),
    DRAFT_SAVED("draft_saved"),
    PUBLISHED("published"),
    NO_IMAGE("no_image"),
    IMAGE_RESOLVED("image_resolved");

    private final String value;

    EditorEventStage(String value) {
        this.value = value;
    }

    @JsonValue
    public String getValue() {
        return value;
    }

    @JsonCreator
    public static EditorEventStage fromValue(String value) {
        for (EditorEventStage stage : values()) {
            if (stage.value.equals(value)) {
                return stage;
            }
        }
        throw new IllegalArgumentException("Unsupported editor event stage");
    }
}
