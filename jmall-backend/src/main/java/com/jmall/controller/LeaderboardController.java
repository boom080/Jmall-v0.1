package com.jmall.controller;

import com.jmall.common.R;
import com.jmall.service.LeaderboardService;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/leaderboard")
public class LeaderboardController {

    private final LeaderboardService leaderboardService;

    public LeaderboardController(LeaderboardService leaderboardService) {
        this.leaderboardService = leaderboardService;
    }

    @GetMapping("/spenders")
    public R getTopSpenders(@RequestParam(required = false, defaultValue = "all") String period) {
        return leaderboardService.getTopSpenders(period);
    }

    @GetMapping("/sellers")
    public R getTopSellers(@RequestParam(required = false, defaultValue = "all") String period) {
        return leaderboardService.getTopSellers(period);
    }

    @GetMapping("/products")
    public R getTopProducts(@RequestParam(required = false, defaultValue = "all") String period) {
        return leaderboardService.getTopProducts(period);
    }
}
