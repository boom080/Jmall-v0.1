package com.jmall.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;

public record PublishCheckResult(
        boolean publishable,
        @JsonProperty("publish_blockers") List<PublishBlocker> publishBlockers) {
}
