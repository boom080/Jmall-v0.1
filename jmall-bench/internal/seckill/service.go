package seckill

import (
	"errors"
	"strings"
	"time"
)

type Clock interface {
	Now() time.Time
}

type ClockFunc func() time.Time

func (f ClockFunc) Now() time.Time {
	return f()
}

type Service struct {
	store  Store
	clock  Clock
	config Config
}

func NewService(store Store, clock Clock, config Config) *Service {
	return &Service{store: store, clock: clock, config: config}
}

func (s *Service) Warmup(request WarmupRequest) (Activity, error) {
	if strings.TrimSpace(request.ActivityID) == "" {
		return Activity{}, errors.New("activityId is required")
	}
	if request.SkuID <= 0 {
		return Activity{}, errors.New("skuId must be positive")
	}
	if request.Stock <= 0 {
		return Activity{}, errors.New("stock must be positive")
	}

	startAt, err := parseTimeOrDefault(request.StartAt, s.clock.Now())
	if err != nil {
		return Activity{}, err
	}
	endAt, err := parseTimeOrDefault(request.EndAt, startAt.Add(30*time.Minute))
	if err != nil {
		return Activity{}, err
	}
	if !endAt.After(startAt) {
		return Activity{}, errors.New("endAt must be after startAt")
	}

	activity := Activity{
		ActivityID: strings.TrimSpace(request.ActivityID),
		SkuID:      request.SkuID,
		Stock:      request.Stock,
		StartAt:    startAt,
		EndAt:      endAt,
	}
	return activity, s.store.Warmup(activity)
}

func (s *Service) Purchase(request PurchaseRequest) PurchaseResult {
	request.ActivityID = strings.TrimSpace(request.ActivityID)
	request.UserID = strings.TrimSpace(request.UserID)
	request.RequestID = strings.TrimSpace(request.RequestID)
	if request.Quantity == 0 {
		request.Quantity = 1
	}
	if request.ActivityID == "" || request.SkuID <= 0 || request.UserID == "" || request.RequestID == "" || request.Quantity <= 0 {
		return PurchaseResult{Accepted: false, Code: "INVALID_REQUEST", Message: "activityId, skuId, userId, requestId and positive quantity are required"}
	}

	now := s.clock.Now()
	orderToken := s.config.BuildOrderToken(request.ActivityID, request.RequestID)
	remaining, eventID, err := s.store.TryPurchase(request, orderToken, now)
	switch {
	case err == nil:
		return PurchaseResult{
			Accepted:         true,
			Code:             "ACCEPTED",
			Message:          "request accepted; Java order service should consume the Redis Stream event",
			ActivityID:       request.ActivityID,
			SeckillSessionID: request.ActivityID,
			SkuID:            request.SkuID,
			UserID:           request.UserID,
			RequestID:        request.RequestID,
			Quantity:         request.Quantity,
			OrderToken:       orderToken,
			Remaining:        remaining,
			StreamEvent:      eventID,
		}
	case errors.Is(err, ErrDuplicateRequest):
		return PurchaseResult{Accepted: false, Code: "DUPLICATE_REQUEST", Message: "user already submitted this activity", ActivityID: request.ActivityID, SeckillSessionID: request.ActivityID, SkuID: request.SkuID, UserID: request.UserID, RequestID: request.RequestID, Quantity: request.Quantity, OrderToken: orderToken, Remaining: remaining, StreamEvent: eventID}
	case errors.Is(err, ErrSoldOut):
		return PurchaseResult{Accepted: false, Code: "SOLD_OUT", Message: "activity stock is sold out", ActivityID: request.ActivityID, SeckillSessionID: request.ActivityID, SkuID: request.SkuID, UserID: request.UserID, RequestID: request.RequestID, Quantity: request.Quantity, OrderToken: orderToken, Remaining: remaining}
	case errors.Is(err, ErrNotStarted):
		return PurchaseResult{Accepted: false, Code: "NOT_STARTED", Message: "activity has not started", ActivityID: request.ActivityID, SeckillSessionID: request.ActivityID, SkuID: request.SkuID, UserID: request.UserID, RequestID: request.RequestID, Quantity: request.Quantity, OrderToken: orderToken, Remaining: remaining}
	case errors.Is(err, ErrEnded):
		return PurchaseResult{Accepted: false, Code: "ENDED", Message: "activity has ended", ActivityID: request.ActivityID, SeckillSessionID: request.ActivityID, SkuID: request.SkuID, UserID: request.UserID, RequestID: request.RequestID, Quantity: request.Quantity, OrderToken: orderToken, Remaining: remaining}
	case errors.Is(err, ErrActivityNotFound):
		return PurchaseResult{Accepted: false, Code: "ACTIVITY_NOT_FOUND", Message: "activity is not warmed up", ActivityID: request.ActivityID, SeckillSessionID: request.ActivityID, SkuID: request.SkuID, UserID: request.UserID, RequestID: request.RequestID, Quantity: request.Quantity, OrderToken: orderToken}
	default:
		return PurchaseResult{Accepted: false, Code: "INTERNAL_ERROR", Message: err.Error(), ActivityID: request.ActivityID, SeckillSessionID: request.ActivityID, SkuID: request.SkuID, UserID: request.UserID, RequestID: request.RequestID, Quantity: request.Quantity, OrderToken: orderToken}
	}
}

func parseTimeOrDefault(value string, fallback time.Time) (time.Time, error) {
	if strings.TrimSpace(value) == "" {
		return fallback, nil
	}
	return time.Parse(time.RFC3339, value)
}
