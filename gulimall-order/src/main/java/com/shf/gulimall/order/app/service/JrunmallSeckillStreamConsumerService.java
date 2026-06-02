package com.shf.gulimall.order.app.service;

import com.shf.gulimall.order.app.dto.SeckillOrderEvent;
import com.shf.gulimall.order.config.JrunmallSeckillProperties;
import io.lettuce.core.Consumer;
import io.lettuce.core.StreamMessage;
import io.lettuce.core.XReadArgs;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.dao.DataAccessException;
import org.springframework.data.redis.connection.DecoratedRedisConnection;
import org.springframework.data.redis.connection.RedisConnection;
import org.springframework.data.redis.connection.lettuce.LettuceConnection;
import org.springframework.data.redis.core.RedisCallback;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

import java.nio.charset.StandardCharsets;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.time.Duration;
import java.util.Date;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.TimeZone;

@Service
public class JrunmallSeckillStreamConsumerService {

    private static final Logger log = LoggerFactory.getLogger(JrunmallSeckillStreamConsumerService.class);
    private static final String XACK_LUA =
            "return redis.call('XACK', KEYS[1], ARGV[1], ARGV[2])";

    private final StringRedisTemplate stringRedisTemplate;
    private final JrunmallSeckillOrderService orderService;
    private final JrunmallSeckillProperties properties;

    public JrunmallSeckillStreamConsumerService(StringRedisTemplate stringRedisTemplate,
                                                JrunmallSeckillOrderService orderService,
                                                JrunmallSeckillProperties properties) {
        this.stringRedisTemplate = stringRedisTemplate;
        this.orderService = orderService;
        this.properties = properties;
    }

    public void ensureConsumerGroup() {
        execute("XGROUP",
                bytes("CREATE"),
                bytes(properties.getStreamName()),
                bytes(properties.getConsumerGroup()),
                bytes("0"),
                bytes("MKSTREAM"));
    }

    public int consumeOnce() {
        ensureConsumerGroup();
        List<StreamMessage<String, String>> messages = readGroup(">", true);
        log.info("consumeOnce stream messages: {}", messages == null ? 0 : messages.size());
        return consumeMessages(messages, false);
    }

    public int retryPendingOnce() {
        ensureConsumerGroup();
        List<StreamMessage<String, String>> messages = readGroup("0", false);
        log.info("retryPendingOnce stream messages: {}", messages == null ? 0 : messages.size());
        return consumeMessages(messages, true);
    }

    int consumeMessages(List<StreamMessage<String, String>> messages, boolean retryingPending) {
        int consumed = 0;
        if (messages == null || messages.isEmpty()) {
            return consumed;
        }
        for (StreamMessage<String, String> message : messages) {
            Map<String, String> body = toBody(message);
            if (isSeckillRecord(body)) {
                consumed += processRecord(body, retryingPending);
            } else {
                log.warn("skip unexpected seckill stream message: stream={}, id={}, bodyKeys={}",
                        message.getStream(), message.getId(), body.keySet());
            }
        }
        return consumed;
    }

    private boolean isSeckillRecord(Map<String, String> body) {
        return body != null
                && !body.isEmpty()
                && body.containsKey("_id")
                && body.containsKey("requestId")
                && body.containsKey("orderToken");
    }

    private int processRecord(Map<String, String> body, boolean retryingPending) {
        String messageId = body.get("_id");
        try {
            orderService.createSeckillOrder(toEvent(body));
            ack(messageId);
            clearRetry(messageId);
            return 1;
        } catch (Exception ex) {
            int retryCount = incrementRetry(messageId);
            if (retryingPending && shouldDeadLetter(retryCount)) {
                deadLetter(messageId, body, ex.getMessage());
                ack(messageId);
                clearRetry(messageId);
                return 1;
            }
            return 0;
        }
    }

    @SuppressWarnings("unchecked")
    private List<StreamMessage<String, String>> readGroup(String offset, boolean block) {
        return stringRedisTemplate.execute(new RedisCallback<List<StreamMessage<String, String>>>() {
            @Override
            public List<StreamMessage<String, String>> doInRedis(RedisConnection connection) throws DataAccessException {
                LettuceConnection lettuceConnection = unwrapLettuceConnection(connection);
                io.lettuce.core.cluster.api.async.RedisClusterAsyncCommands<byte[], byte[]> nativeConnection =
                        lettuceConnection.getNativeConnection();
                Consumer<byte[]> consumer = Consumer.from(
                        bytes(properties.getConsumerGroup()),
                        bytes(properties.getConsumerName()));
                XReadArgs.StreamOffset<byte[]> streamOffset = block
                        ? XReadArgs.StreamOffset.from(bytes(properties.getStreamName()), ">")
                        : XReadArgs.StreamOffset.from(bytes(properties.getStreamName()), offset);
                XReadArgs args = new XReadArgs().count(10);
                if (block) {
                    args.block(Duration.ofMillis(100));
                }
                try {
                    List<StreamMessage<byte[], byte[]>> messages = nativeConnection
                            .xreadgroup(consumer, args, streamOffset)
                            .get(5, java.util.concurrent.TimeUnit.SECONDS);
                    return (List<StreamMessage<String, String>>) (List<?>) messages;
                } catch (Exception ex) {
                    throw new IllegalStateException("failed to read seckill stream group messages", ex);
                }
            }
        });
    }

    private LettuceConnection unwrapLettuceConnection(RedisConnection connection) {
        RedisConnection current = connection;
        while (current instanceof DecoratedRedisConnection) {
            RedisConnection delegate = ((DecoratedRedisConnection) current).getDelegate();
            if (delegate == null || delegate == current) {
                break;
            }
            current = delegate;
        }
        if (current instanceof LettuceConnection) {
            return (LettuceConnection) current;
        }
        throw new IllegalStateException("Jrunmall seckill stream consumer requires LettuceConnection but got "
                + (current == null ? "null" : current.getClass().getName()));
    }

    SeckillOrderEvent toEvent(Map<String, String> body) {
        SeckillOrderEvent event = new SeckillOrderEvent();
        event.setRequestId(body.get("requestId"));
        event.setUserId(parseLong(body.get("userId")));
        event.setSkuId(parseLong(body.get("skuId")));
        event.setQuantity(parseInt(body.get("quantity"), 1));
        event.setSeckillSessionId(body.get("seckillSessionId"));
        event.setOrderToken(body.get("orderToken"));
        event.setTimestamp(parseTimestamp(body.get("timestamp")));
        return event;
    }

    boolean shouldDeadLetter(int retryCount) {
        return retryCount >= properties.getMaxRetryCount();
    }

    private void deadLetter(String messageId, Map<String, String> body, String reason) {
        execute("XADD",
                bytes(properties.getDeadLetterStreamName()),
                bytes("*"),
                bytes("originalMessageId"),
                bytes(nullToEmpty(messageId)),
                bytes("requestId"),
                bytes(nullToEmpty(body.get("requestId"))),
                bytes("orderToken"),
                bytes(nullToEmpty(body.get("orderToken"))),
                bytes("reason"),
                bytes(nullToEmpty(reason)),
                bytes("deadAt"),
                bytes(String.valueOf(System.currentTimeMillis())));
    }

    private int incrementRetry(String messageId) {
        if (messageId == null || messageId.trim().isEmpty()) {
            return properties.getMaxRetryCount();
        }
        Long count = stringRedisTemplate.opsForValue().increment(retryKey(messageId));
        return count == null ? 0 : count.intValue();
    }

    private void clearRetry(String messageId) {
        if (messageId != null && !messageId.trim().isEmpty()) {
            stringRedisTemplate.delete(retryKey(messageId));
        }
    }

    private String retryKey(String messageId) {
        return properties.getRetryCountKeyPrefix() + ":" + messageId;
    }

    private void ack(String messageId) {
        if (messageId == null || messageId.trim().isEmpty()) {
            return;
        }
        Long acked = stringRedisTemplate.execute(new RedisCallback<Long>() {
            @Override
            public Long doInRedis(RedisConnection connection) throws DataAccessException {
                try {
                    Object result = connection.execute("EVAL",
                            bytes(XACK_LUA),
                            bytes("1"),
                            bytes(properties.getStreamName()),
                            bytes(properties.getConsumerGroup()),
                            bytes(messageId.trim()));
                    return result instanceof Number ? ((Number) result).longValue() : 0L;
                } catch (Exception ex) {
                    throw new IllegalStateException("failed to ack seckill stream message " + messageId, ex);
                }
            }
        });
        log.info("xack messageId={}, acked={}", messageId, acked);
    }

    private Object execute(final String command, final byte[]... args) {
        try {
            return stringRedisTemplate.execute(new RedisCallback<Object>() {
                @Override
                public Object doInRedis(RedisConnection connection) throws DataAccessException {
                    return connection.execute(command, args);
                }
            });
        } catch (Exception ex) {
            if ("XGROUP".equals(command) && ex.getMessage() != null && ex.getMessage().contains("BUSYGROUP")) {
                return null;
            }
            throw ex;
        }
    }

    private Map<String, String> toBody(StreamMessage<?, ?> message) {
        Map<String, String> body = new LinkedHashMap<String, String>();
        if (message == null) {
            return body;
        }
        body.put("_id", asString(message.getId()));
        if (message.getBody() != null) {
            for (Map.Entry<?, ?> entry : message.getBody().entrySet()) {
                body.put(asString(entry.getKey()), asString(entry.getValue()));
            }
        }
        return body;
    }

    private byte[] bytes(String value) {
        return nullToEmpty(value).getBytes(StandardCharsets.UTF_8);
    }

    private String asString(Object value) {
        if (value instanceof byte[]) {
            return new String((byte[]) value, StandardCharsets.UTF_8);
        }
        return value == null ? "" : String.valueOf(value);
    }

    private String nullToEmpty(String value) {
        return value == null ? "" : value;
    }

    private Long parseLong(String value) {
        try {
            return Long.valueOf(value);
        } catch (Exception ex) {
            return null;
        }
    }

    private Integer parseInt(String value, Integer fallback) {
        try {
            return Integer.valueOf(value);
        } catch (Exception ex) {
            return fallback;
        }
    }

    private Date parseTimestamp(String value) {
        if (value == null || value.trim().isEmpty()) {
            return new Date();
        }
        SimpleDateFormat format = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'", Locale.ROOT);
        format.setTimeZone(TimeZone.getTimeZone("UTC"));
        try {
            return format.parse(value);
        } catch (ParseException ex) {
            return new Date();
        }
    }
}





