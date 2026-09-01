package com.jmall.dto;

import jakarta.validation.constraints.NotNull;
import lombok.Data;

import java.util.UUID;

@Data
public class EditorEventRequest {

    @NotNull
    private UUID sessionId;

    @NotNull
    private EditorEventStage stage;
}
