package seckill

import (
	"context"
	"errors"
	"fmt"
	"sync"
	"time"

	"github.com/redis/go-redis/v9"
)

var (
	ErrActivityNotFound = errors.New("activity not found")
	ErrDuplicateRequest = errors.New("duplicate request")
	ErrSoldOut          = errors.New("sold out")
	ErrNotStarted       = errors.New("activity not started")
	ErrEnded            = errors.New("activity ended")
)

type Store interface {
	Warmup(activity Activity) error
	TryPurchase(request PurchaseRequest, orderToken string, timestamp time.Time) (int, string, error)
}

type MemoryStore struct {
	mu         sync.Mutex
	activities map[string]Activity
	requests   map[string]PurchaseResult
	eventSeq   int64
}

func NewMemoryStore() *MemoryStore {
	return &MemoryStore{
		activities: map[string]Activity{},
		requests:   map[string]PurchaseResult{},
	}
}

func (s *MemoryStore) Warmup(activity Activity) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	s.activities[activity.ActivityID] = activity
	return nil
}

func (s *MemoryStore) TryPurchase(request PurchaseRequest, orderToken string, timestamp time.Time) (int, string, error) {
	s.mu.Lock()
	defer s.mu.Unlock()

	if existing, ok := s.requests[request.RequestID]; ok {
		return existing.Remaining, existing.StreamEvent, ErrDuplicateRequest
	}

	activity, ok := s.activities[request.ActivityID]
	if !ok {
		return 0, "", ErrActivityNotFound
	}
	if timestamp.Before(activity.StartAt) {
		return activity.Stock, "", ErrNotStarted
	}
	if timestamp.After(activity.EndAt) {
		return activity.Stock, "", ErrEnded
	}
	if activity.Stock < request.Quantity {
		return 0, "", ErrSoldOut
	}

	activity.Stock -= request.Quantity
	s.activities[request.ActivityID] = activity
	s.eventSeq++
	eventID := fmt.Sprintf("memory-stream:jrunmall:seckill:orders:%d", s.eventSeq)
	s.requests[request.RequestID] = PurchaseResult{
		Accepted:         true,
		Code:             "ACCEPTED",
		ActivityID:       request.ActivityID,
		SeckillSessionID: request.ActivityID,
		UserID:           request.UserID,
		RequestID:        request.RequestID,
		SkuID:            request.SkuID,
		Quantity:         request.Quantity,
		OrderToken:       orderToken,
		Remaining:        activity.Stock,
		StreamEvent:      eventID,
		Message:          timestamp.UTC().Format(time.RFC3339),
	}
	return activity.Stock, eventID, nil
}

type RedisStore struct {
	client RedisClient
	config Config
}

type RedisClient interface {
	Eval(ctx context.Context, script string, keys []string, args ...interface{}) *redis.Cmd
	HSet(ctx context.Context, key string, values ...interface{}) *redis.IntCmd
	Expire(ctx context.Context, key string, expiration time.Duration) *redis.BoolCmd
}

func NewRedisStore(client RedisClient, config Config) *RedisStore {
	return &RedisStore{client: client, config: config}
}

func (s *RedisStore) Warmup(activity Activity) error {
	ctx := context.Background()
	activityKey := s.config.ActivityKey(activity.ActivityID)
	if err := s.client.HSet(ctx, activityKey,
		"activityId", activity.ActivityID,
		"skuId", activity.SkuID,
		"stock", activity.Stock,
		"startAt", activity.StartAt.UTC().Format(time.RFC3339),
		"endAt", activity.EndAt.UTC().Format(time.RFC3339),
	).Err(); err != nil {
		return err
	}
	if err := s.client.HSet(ctx, s.config.StockKey(activity.ActivityID), "stock", activity.Stock).Err(); err != nil {
		return err
	}
	_ = s.client.Expire(ctx, activityKey, 24*time.Hour).Err()
	_ = s.client.Expire(ctx, s.config.StockKey(activity.ActivityID), 24*time.Hour).Err()
	return nil
}

func (s *RedisStore) TryPurchase(request PurchaseRequest, orderToken string, timestamp time.Time) (int, string, error) {
	ctx := context.Background()
	keys := []string{
		s.config.StockKey(request.ActivityID),
		s.config.IdempotencyKey(request.ActivityID, request.UserID),
		s.config.RequestKey(request.RequestID),
		s.config.StreamName,
		s.config.ActivityKey(request.ActivityID),
	}
	result, err := s.client.Eval(ctx, seckillLuaScript, keys,
		request.Quantity,
		request.RequestID,
		request.UserID,
		request.SkuID,
		request.ActivityID,
		orderToken,
		timestamp.UTC().Format(time.RFC3339),
	).Result()
	if err != nil {
		return 0, "", err
	}
	values, ok := result.([]interface{})
	if !ok || len(values) < 3 {
		return 0, "", fmt.Errorf("unexpected redis script result: %v", result)
	}
	code := fmt.Sprint(values[0])
	remaining := toInt(values[1])
	eventID := fmt.Sprint(values[2])
	switch code {
	case "ACCEPTED":
		return remaining, eventID, nil
	case "DUPLICATE_REQUEST":
		return remaining, eventID, ErrDuplicateRequest
	case "SOLD_OUT":
		return remaining, "", ErrSoldOut
	case "NOT_STARTED":
		return remaining, "", ErrNotStarted
	case "ENDED":
		return remaining, "", ErrEnded
	case "ACTIVITY_NOT_FOUND":
		return remaining, "", ErrActivityNotFound
	default:
		return remaining, "", fmt.Errorf("unexpected redis script code: %s", code)
	}
}

func toInt(value interface{}) int {
	switch v := value.(type) {
	case int:
		return v
	case int64:
		return int(v)
	case uint64:
		return int(v)
	default:
		return 0
	}
}

const seckillLuaScript = `
local stockHash = KEYS[1]
local idemKey = KEYS[2]
local requestKey = KEYS[3]
local streamName = KEYS[4]
local activityKey = KEYS[5]
local quantity = tonumber(ARGV[1])
local requestId = ARGV[2]
local userId = ARGV[3]
local skuId = ARGV[4]
local activityId = ARGV[5]
local orderToken = ARGV[6]
local timestamp = ARGV[7]

if redis.call("EXISTS", activityKey) == 0 or redis.call("EXISTS", stockHash) == 0 then
  return {"ACTIVITY_NOT_FOUND", 0, ""}
end

if redis.call("EXISTS", idemKey) == 1 then
  local remaining = tonumber(redis.call("HGET", stockHash, "stock") or "0")
  local eventId = redis.call("GET", requestKey) or ""
  return {"DUPLICATE_REQUEST", remaining, eventId}
end

local startAt = redis.call("HGET", activityKey, "startAt") or ""
local endAt = redis.call("HGET", activityKey, "endAt") or ""
if startAt ~= "" and timestamp < startAt then
  local remaining = tonumber(redis.call("HGET", stockHash, "stock") or "0")
  return {"NOT_STARTED", remaining, ""}
end
if endAt ~= "" and timestamp > endAt then
  local remaining = tonumber(redis.call("HGET", stockHash, "stock") or "0")
  return {"ENDED", remaining, ""}
end

local stock = tonumber(redis.call("HGET", stockHash, "stock") or "-1")
if stock < quantity then
  return {"SOLD_OUT", stock, ""}
end

local remaining = stock - quantity
redis.call("HSET", stockHash, "stock", remaining)
redis.call("SET", idemKey, requestId, "EX", 86400)
local eventId = redis.call("XADD", streamName, "*",
  "requestId", requestId,
  "userId", userId,
  "skuId", skuId,
  "quantity", tostring(quantity),
  "seckillSessionId", activityId,
  "orderToken", orderToken,
  "timestamp", timestamp
)
redis.call("SET", requestKey, eventId, "EX", 86400)
return {"ACCEPTED", remaining, eventId}
`
