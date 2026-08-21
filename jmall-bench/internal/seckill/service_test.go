package seckill

import (
	"testing"
	"time"
)

func TestWarmupAndPurchaseAccepted(t *testing.T) {
	service := NewService(NewMemoryStore(), ClockFunc(func() time.Time {
		return time.Date(2026, 4, 29, 12, 0, 0, 0, time.UTC)
	}), LoadConfig())

	_, err := service.Warmup(WarmupRequest{
		ActivityID: "flash-20260429",
		SkuID:      14,
		Stock:      2,
	})
	if err != nil {
		t.Fatalf("warmup failed: %v", err)
	}

	result := service.Purchase(PurchaseRequest{
		ActivityID: "flash-20260429",
		SkuID:      14,
		UserID:     "900001",
		RequestID:  "req-1",
		Quantity:   1,
	})

	if !result.Accepted {
		t.Fatalf("expected accepted purchase, got %+v", result)
	}
	if result.Remaining != 1 {
		t.Fatalf("expected remaining stock 1, got %d", result.Remaining)
	}
	if result.StreamEvent == "" {
		t.Fatal("expected stream event id")
	}
	if result.OrderToken != "SEC-flash-20260429-req-1" {
		t.Fatalf("expected deterministic order token, got %s", result.OrderToken)
	}
}

func TestPurchaseRejectsDuplicateRequest(t *testing.T) {
	service := NewService(NewMemoryStore(), ClockFunc(time.Now), LoadConfig())
	_, _ = service.Warmup(WarmupRequest{ActivityID: "flash-1", SkuID: 14, Stock: 1})

	first := service.Purchase(PurchaseRequest{ActivityID: "flash-1", SkuID: 14, UserID: "900001", RequestID: "same"})
	second := service.Purchase(PurchaseRequest{ActivityID: "flash-1", SkuID: 14, UserID: "900001", RequestID: "same"})

	if !first.Accepted {
		t.Fatalf("first request should be accepted")
	}
	if second.Code != "DUPLICATE_REQUEST" {
		t.Fatalf("expected duplicate rejection, got %s", second.Code)
	}
}

func TestPurchaseRejectsSoldOut(t *testing.T) {
	service := NewService(NewMemoryStore(), ClockFunc(time.Now), LoadConfig())
	_, _ = service.Warmup(WarmupRequest{ActivityID: "flash-1", SkuID: 14, Stock: 1})

	_ = service.Purchase(PurchaseRequest{ActivityID: "flash-1", SkuID: 14, UserID: "900001", RequestID: "req-1"})
	result := service.Purchase(PurchaseRequest{ActivityID: "flash-1", SkuID: 14, UserID: "900002", RequestID: "req-2"})

	if result.Code != "SOLD_OUT" {
		t.Fatalf("expected sold out, got %s", result.Code)
	}
}

func TestConfigBuildsRedisKeys(t *testing.T) {
	config := Config{KeyPrefix: "jrunmall:seckill", OrderTokenPrefix: "SEC"}

	if config.StockKey("flash-1") != "jrunmall:seckill:stock:flash-1" {
		t.Fatalf("unexpected stock key: %s", config.StockKey("flash-1"))
	}
	if config.IdempotencyKey("flash-1", "900001") != "jrunmall:seckill:idem:flash-1:900001" {
		t.Fatalf("unexpected idempotency key: %s", config.IdempotencyKey("flash-1", "900001"))
	}
	if config.BuildOrderToken("flash-1", "req-1") != "SEC-flash-1-req-1" {
		t.Fatalf("unexpected order token: %s", config.BuildOrderToken("flash-1", "req-1"))
	}
}
