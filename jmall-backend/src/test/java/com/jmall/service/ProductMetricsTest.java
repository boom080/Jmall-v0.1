package com.jmall.service;

import com.jmall.dto.EditorEventStage;
import io.micrometer.core.instrument.simple.SimpleMeterRegistry;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.transaction.support.TransactionSynchronizationManager;
import org.springframework.transaction.support.TransactionSynchronizationUtils;

import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneId;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.springframework.transaction.support.TransactionSynchronization.STATUS_ROLLED_BACK;

class ProductMetricsTest {

    private SimpleMeterRegistry registry;
    private ProductMetrics metrics;

    @BeforeEach
    void setUp() {
        registry = new SimpleMeterRegistry();
        metrics = new ProductMetrics(registry, Clock.systemUTC());
    }

    @AfterEach
    void tearDown() {
        if (TransactionSynchronizationManager.isSynchronizationActive()) {
            TransactionSynchronizationManager.clearSynchronization();
        }
    }

    @Test
    void editorStagesRequireOpenedAndAreDeduplicatedPerUserSession() {
        UUID sessionId = UUID.randomUUID();

        assertFalse(metrics.recordEditorEvent(7L, sessionId, EditorEventStage.DRAFT_SAVED));
        assertTrue(metrics.recordEditorEvent(7L, sessionId, EditorEventStage.EDITOR_OPENED));
        assertFalse(metrics.recordEditorEvent(7L, sessionId, EditorEventStage.EDITOR_OPENED));
        assertTrue(metrics.recordEditorEvent(7L, sessionId, EditorEventStage.DRAFT_SAVED));
        assertFalse(metrics.recordEditorEvent(7L, sessionId, EditorEventStage.DRAFT_SAVED));

        assertEquals(1, countEditor("editor_opened"));
        assertEquals(1, countEditor("draft_saved"));
    }

    @Test
    void editorSessionsAreIsolatedByUserId() {
        UUID sessionId = UUID.randomUUID();

        assertTrue(metrics.recordEditorEvent(7L, sessionId, EditorEventStage.EDITOR_OPENED));
        assertFalse(metrics.recordEditorEvent(8L, sessionId, EditorEventStage.DRAFT_SAVED));
        assertTrue(metrics.recordEditorEvent(8L, sessionId, EditorEventStage.EDITOR_OPENED));
        assertTrue(metrics.recordEditorEvent(8L, sessionId, EditorEventStage.DRAFT_SAVED));

        assertEquals(2, countEditor("editor_opened"));
        assertEquals(1, countEditor("draft_saved"));
    }

    @Test
    void conversionStagesRequireTheirPredecessors() {
        UUID sessionId = UUID.randomUUID();

        assertTrue(metrics.recordEditorEvent(7L, sessionId, EditorEventStage.EDITOR_OPENED));
        assertFalse(metrics.recordEditorEvent(7L, sessionId, EditorEventStage.PUBLISHED));
        assertFalse(metrics.recordEditorEvent(7L, sessionId, EditorEventStage.IMAGE_RESOLVED));
        assertTrue(metrics.recordEditorEvent(7L, sessionId, EditorEventStage.NO_IMAGE));
        assertTrue(metrics.recordEditorEvent(7L, sessionId, EditorEventStage.IMAGE_RESOLVED));
        assertTrue(metrics.recordEditorEvent(7L, sessionId, EditorEventStage.DRAFT_SAVED));
        assertTrue(metrics.recordEditorEvent(7L, sessionId, EditorEventStage.PUBLISHED));

        assertEquals(1, countEditor("no_image"));
        assertEquals(1, countEditor("image_resolved"));
        assertEquals(1, countEditor("draft_saved"));
        assertEquals(1, countEditor("published"));
    }

    @Test
    void expiredEditorEventsCanNoLongerCreateDownstreamStages() {
        AdjustableClock clock = new AdjustableClock(Instant.parse("2026-01-01T00:00:00Z"));
        metrics = new ProductMetrics(registry, clock);
        UUID sessionId = UUID.randomUUID();

        assertTrue(metrics.recordEditorEvent(7L, sessionId, EditorEventStage.EDITOR_OPENED));
        clock.advance(ProductMetrics.EDITOR_EVENT_TTL.plusMillis(1));

        assertFalse(metrics.recordEditorEvent(7L, sessionId, EditorEventStage.DRAFT_SAVED));
        assertEquals(0, metrics.editorEventCacheSize());
        assertEquals(0, countEditor("draft_saved"));
    }

    @Test
    void editorEventCacheIsBounded() {
        for (int i = 0; i < ProductMetrics.MAX_EDITOR_EVENT_CACHE_ENTRIES + 1; i++) {
            assertTrue(metrics.recordEditorEvent(7L, UUID.nameUUIDFromBytes(
                    ("editor-session-" + i).getBytes()), EditorEventStage.EDITOR_OPENED));
        }

        assertEquals(ProductMetrics.MAX_EDITOR_EVENT_CACHE_ENTRIES, metrics.editorEventCacheSize());
        assertFalse(metrics.recordEditorEvent(7L, UUID.nameUUIDFromBytes(
                "editor-session-0".getBytes()), EditorEventStage.DRAFT_SAVED));
    }

    @Test
    void productEventsIncrementOnlyAfterCommit() {
        TransactionSynchronizationManager.initSynchronization();
        metrics.recordProductEventAfterCommit(ProductMetrics.ProductEvent.DRAFT_CREATED);
        assertEquals(0, countProduct("draft_created"));

        TransactionSynchronizationUtils.triggerAfterCommit();
        TransactionSynchronizationManager.clearSynchronization();
        assertEquals(1, countProduct("draft_created"));

        TransactionSynchronizationManager.initSynchronization();
        metrics.recordProductEventAfterCommit(ProductMetrics.ProductEvent.PUBLISHED);
        TransactionSynchronizationUtils.triggerAfterCompletion(STATUS_ROLLED_BACK);
        TransactionSynchronizationManager.clearSynchronization();
        assertEquals(0, countProduct("published"));
    }

    private double countEditor(String stage) {
        return registry.get("jmall_editor_sessions_total").tag("stage", stage).counter().count();
    }

    private double countProduct(String event) {
        return registry.get("jmall_product_events_total").tag("event", event).counter().count();
    }

    private static final class AdjustableClock extends Clock {
        private Instant current;

        private AdjustableClock(Instant current) {
            this.current = current;
        }

        private void advance(Duration duration) {
            current = current.plus(duration);
        }

        @Override
        public ZoneId getZone() {
            return ZoneId.of("UTC");
        }

        @Override
        public Clock withZone(ZoneId zone) {
            return this;
        }

        @Override
        public Instant instant() {
            return current;
        }
    }
}
