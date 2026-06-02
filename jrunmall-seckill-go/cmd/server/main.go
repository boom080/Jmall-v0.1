package main

import (
	"log"
	"net/http"
	"time"

	"github.com/redis/go-redis/v9"
	"jrunmall-seckill-go/internal/seckill"
)

func main() {
	config := seckill.LoadConfig()
	store := buildStore(config)
	service := seckill.NewService(store, seckill.ClockFunc(time.Now), config)
	handler := seckill.NewHandler(service)

	log.Printf("jrunmall seckill go service listening on http://%s", config.Addr)
	if config.RedisURL == "" {
		log.Printf("JRUNMALL_SECKILL_REDIS_URL is empty; using in-memory store for local tests")
	} else {
		log.Printf("using Redis Streams stream=%s", config.StreamName)
	}
	if err := http.ListenAndServe(config.Addr, handler.Routes()); err != nil {
		log.Fatal(err)
	}
}

func buildStore(config seckill.Config) seckill.Store {
	if config.RedisURL == "" {
		return seckill.NewMemoryStore()
	}
	options, err := redis.ParseURL(config.RedisURL)
	if err != nil {
		log.Printf("invalid JRUNMALL_SECKILL_REDIS_URL, falling back to memory store: %v", err)
		return seckill.NewMemoryStore()
	}
	return seckill.NewRedisStore(redis.NewClient(options), config)
}
