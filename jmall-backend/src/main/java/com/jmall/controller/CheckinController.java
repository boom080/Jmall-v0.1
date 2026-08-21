package com.jmall.controller;

import com.jmall.common.R;
import com.jmall.service.CheckinService;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/checkin")
public class CheckinController {

    private final CheckinService checkinService;

    public CheckinController(CheckinService checkinService) {
        this.checkinService = checkinService;
    }

    @PostMapping
    public R checkin() {
        return checkinService.checkin();
    }

    @GetMapping("/today")
    public R todayStatus() {
        return checkinService.getTodayStatus();
    }
}
