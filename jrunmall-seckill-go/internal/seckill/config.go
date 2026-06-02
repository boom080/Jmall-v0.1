package seckill

import (
	"os"
	"strings"
)

type Config struct {
	Addr              string
	RedisURL          string
	StreamName        string
	KeyPrefix         string
	OrderTokenPrefix  string
}

func LoadConfig() Config {
	return Config{
		Addr:             env("JRUNMALL_SECKILL_ADDR", "127.0.0.1:19090"),
		RedisURL:         os.Getenv("JRUNMALL_SECKILL_REDIS_URL"),
		StreamName:       env("JRUNMALL_SECKILL_STREAM", "jrunmall:seckill:orders"),
		KeyPrefix:        strings.TrimRight(env("JRUNMALL_SECKILL_KEY_PREFIX", "jrunmall:seckill"), ":"),
		OrderTokenPrefix: env("JRUNMALL_SECKILL_ORDER_TOKEN_PREFIX", "SEC"),
	}
}

func (c Config) ActivityKey(activityID string) string {
	return c.KeyPrefix + ":activity:" + activityID
}

func (c Config) StockKey(activityID string) string {
	return c.KeyPrefix + ":stock:" + activityID
}

func (c Config) IdempotencyKey(activityID string, userID string) string {
	return c.KeyPrefix + ":idem:" + activityID + ":" + userID
}

func (c Config) RequestKey(requestID string) string {
	return c.KeyPrefix + ":request:" + requestID
}

func (c Config) BuildOrderToken(activityID string, requestID string) string {
	return c.OrderTokenPrefix + "-" + activityID + "-" + requestID
}

func env(key string, fallback string) string {
	value := strings.TrimSpace(os.Getenv(key))
	if value == "" {
		return fallback
	}
	return value
}
