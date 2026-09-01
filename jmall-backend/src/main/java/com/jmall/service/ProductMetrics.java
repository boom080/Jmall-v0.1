package com.jmall.service;

import com.jmall.common.UserContext;
import com.jmall.dto.EditorEventStage;
import io.micrometer.core.instrument.Counter;
import io.micrometer.core.instrument.MeterRegistry;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.support.TransactionSynchronization;
import org.springframework.transaction.support.TransactionSynchronizationManager;

import java.time.Clock;
import java.time.Duration;
import java.util.Collections;
import java.util.EnumMap;
import java.util.EnumSet;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.UUID;

/**
 * Low-cardinality product funnel metrics and the best-effort editor telemetry
 * deduplicator. Identifiers are kept only in the bounded in-memory cache and
 * are never used as metric labels or log fields.
 */
@Service
public class ProductMetrics {

    static final int MAX_EDITOR_EVENT_CACHE_ENTRIES = 10_000;
    static final Duration EDITOR_EVENT_TTL = Duration.ofHours(24);

    private final Map<EditorEventStage, Counter> editorSessionCounters;
    private final Map<ProductEvent, Counter> productEventCounters;
    private final Clock clock;
    private final Object editorCacheLock = new Object();
    private final LinkedHashMap<EditorEventKey, EditorSessionState> editorSessions = new LinkedHashMap<>();
    private final boolean enabled;

    /**
     * Spring's Micrometer registry is provided by the Actuator configuration.
     */
    @Autowired
    public ProductMetrics(MeterRegistry registry) {
        this(registry, Clock.systemUTC());
    }

    ProductMetrics(MeterRegistry registry, Clock clock) {
        this.clock = clock;
        this.enabled = registry != null;
        this.editorSessionCounters = enabled
                ? buildEditorCounters(registry)
                : Collections.emptyMap();
        this.productEventCounters = enabled
                ? buildProductCounters(registry)
                : Collections.emptyMap();
    }

    /**
     * A disabled instance keeps existing direct unit-test constructors
     * compatible while the Spring application always uses the registry-backed
     * constructor above.
     */
    static ProductMetrics disabled() {
        return new ProductMetrics(null, Clock.systemUTC());
    }

    public boolean recordEditorEvent(UUID sessionId, EditorEventStage stage) {
        return recordEditorEvent(UserContext.getUserId(), sessionId, stage);
    }

    /**
     * Record one authenticated browser event. Stages after editor_opened are
     * intentionally ignored when the opening event is absent: accepting them
     * would fabricate a session after a dropped client event.
     */
    public boolean recordEditorEvent(Long userId, UUID sessionId, EditorEventStage stage) {
        if (userId == null || sessionId == null || stage == null) {
            return false;
        }

        long now = clock.millis();
        EditorEventKey key = new EditorEventKey(userId, sessionId);
        synchronized (editorCacheLock) {
            purgeExpiredEditorEvents(now);
            EditorSessionState session = editorSessions.get(key);
            if (!hasPrerequisite(session, stage)) {
                return false;
            }
            if (session != null && session.stages.contains(stage)) {
                return false;
            }
            if (session == null) {
                if (stage != EditorEventStage.EDITOR_OPENED) {
                    return false;
                }
                if (editorSessions.size() >= MAX_EDITOR_EVENT_CACHE_ENTRIES) {
                    editorSessions.remove(editorSessions.keySet().iterator().next());
                }
                session = new EditorSessionState(safeExpiry(now));
                editorSessions.put(key, session);
            }
            session.stages.add(stage);
        }

        increment(editorSessionCounters.get(stage));
        return true;
    }

    /**
     * Record a server-authoritative product event after the current transaction
     * commits. A non-transactional caller records immediately. Metric failures
     * are swallowed so observability cannot change business behavior.
     */
    public void recordProductEventAfterCommit(ProductEvent event) {
        if (event == null) {
            return;
        }
        Runnable increment = () -> increment(productEventCounters.get(event));
        if (TransactionSynchronizationManager.isSynchronizationActive()) {
            try {
                TransactionSynchronizationManager.registerSynchronization(new TransactionSynchronization() {
                    @Override
                    public void afterCommit() {
                        increment.run();
                    }
                });
                return;
            } catch (RuntimeException ignored) {
                // Do not count before commit when synchronization cannot be registered.
                return;
            }
        }
        increment.run();
    }

    Counter editorSessionCounter(EditorEventStage stage) {
        return editorSessionCounters.get(stage);
    }

    Counter productEventCounter(ProductEvent event) {
        return productEventCounters.get(event);
    }

    int editorEventCacheSize() {
        synchronized (editorCacheLock) {
            purgeExpiredEditorEvents(clock.millis());
            return editorSessions.size();
        }
    }

    private Map<EditorEventStage, Counter> buildEditorCounters(MeterRegistry registry) {
        EnumMap<EditorEventStage, Counter> counters = new EnumMap<>(EditorEventStage.class);
        for (EditorEventStage stage : EditorEventStage.values()) {
            try {
                counters.put(stage, Counter.builder("jmall_editor_sessions_total")
                        .description("Editor sessions reaching each client-reported stage")
                        .tag("stage", stage.getValue())
                        .register(registry));
            } catch (RuntimeException ignored) {
                // A broken meter must not prevent the business service from starting.
            }
        }
        return Collections.unmodifiableMap(counters);
    }

    private Map<ProductEvent, Counter> buildProductCounters(MeterRegistry registry) {
        EnumMap<ProductEvent, Counter> counters = new EnumMap<>(ProductEvent.class);
        for (ProductEvent event : ProductEvent.values()) {
            try {
                counters.put(event, Counter.builder("jmall_product_events_total")
                        .description("Server-authoritative product lifecycle events")
                        .tag("event", event.getValue())
                        .register(registry));
            } catch (RuntimeException ignored) {
                // A broken meter must not prevent the business service from starting.
            }
        }
        return Collections.unmodifiableMap(counters);
    }

    private void purgeExpiredEditorEvents(long now) {
        editorSessions.entrySet().removeIf(entry -> entry.getValue().expiresAt <= now);
    }

    private boolean hasPrerequisite(EditorSessionState session, EditorEventStage stage) {
        EditorEventStage prerequisite = switch (stage) {
            case EDITOR_OPENED -> null;
            case DRAFT_SAVED, NO_IMAGE -> EditorEventStage.EDITOR_OPENED;
            case PUBLISHED -> EditorEventStage.DRAFT_SAVED;
            case IMAGE_RESOLVED -> EditorEventStage.NO_IMAGE;
        };
        return prerequisite == null
                || session != null && session.stages.contains(prerequisite);
    }

    private long safeExpiry(long now) {
        long ttlMillis = EDITOR_EVENT_TTL.toMillis();
        return now > Long.MAX_VALUE - ttlMillis ? Long.MAX_VALUE : now + ttlMillis;
    }

    private void increment(Counter counter) {
        if (!enabled || counter == null) {
            return;
        }
        try {
            counter.increment();
        } catch (RuntimeException ignored) {
            // Metrics must never break a product request or transaction callback.
        }
    }

    public enum ProductEvent {
        DRAFT_CREATED("draft_created"),
        DRAFT_SAVED("draft_saved"),
        PUBLISHED("published"),
        PUBLISHED_UPDATED("published_updated"),
        PUBLISH_BLOCKED("publish_blocked");

        private final String value;

        ProductEvent(String value) {
            this.value = value;
        }

        public String getValue() {
            return value;
        }
    }

    private record EditorEventKey(Long userId, UUID sessionId) {
    }

    private static final class EditorSessionState {
        private final long expiresAt;
        private final EnumSet<EditorEventStage> stages = EnumSet.noneOf(EditorEventStage.class);

        private EditorSessionState(long expiresAt) {
            this.expiresAt = expiresAt;
        }
    }
}
