package seckill

import "time"

type Activity struct {
	ActivityID string    `json:"activityId"`
	SkuID      int64     `json:"skuId"`
	Stock      int       `json:"stock"`
	StartAt    time.Time `json:"startAt"`
	EndAt      time.Time `json:"endAt"`
}

type WarmupRequest struct {
	ActivityID string `json:"activityId"`
	SkuID      int64  `json:"skuId"`
	Stock      int    `json:"stock"`
	StartAt    string `json:"startAt"`
	EndAt      string `json:"endAt"`
}

type PurchaseRequest struct {
	ActivityID string `json:"activityId"`
	SkuID      int64  `json:"skuId"`
	UserID     string `json:"userId"`
	RequestID  string `json:"requestId"`
	Quantity   int    `json:"quantity"`
}

type PurchaseResult struct {
	Accepted          bool   `json:"accepted"`
	Code              string `json:"code"`
	Message           string `json:"message"`
	ActivityID        string `json:"activityId"`
	SeckillSessionID  string `json:"seckillSessionId"`
	SkuID             int64  `json:"skuId"`
	UserID            string `json:"userId"`
	RequestID         string `json:"requestId"`
	Quantity          int    `json:"quantity"`
	OrderToken        string `json:"orderToken"`
	Remaining         int    `json:"remaining"`
	StreamEvent       string `json:"streamEvent"`
}

type HealthResponse struct {
	Status  string `json:"status"`
	Service string `json:"service"`
}
