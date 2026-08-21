package com.jmall.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.jmall.common.BizCodeEnum;
import com.jmall.common.R;
import com.jmall.common.UserContext;
import com.jmall.dto.CheckinResponse;
import com.jmall.entity.Checkin;
import com.jmall.entity.User;
import com.jmall.repository.CheckinRepository;
import com.jmall.repository.UserRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.time.LocalDateTime;

@Service
public class CheckinService {

    private final CheckinRepository checkinRepository;
    private final UserRepository userRepository;
    private final UserService userService;
    private final AchievementService achievementService;

    // Constants — 1 gold = 1 yuan
    private static final long BASE_REWARD = 1000L;
    private static final long STREAK_BONUS = 500L;
    private static final int MAX_STREAK = 7;

    public CheckinService(CheckinRepository checkinRepository,
                          UserRepository userRepository,
                          UserService userService,
                          AchievementService achievementService) {
        this.checkinRepository = checkinRepository;
        this.userRepository = userRepository;
        this.userService = userService;
        this.achievementService = achievementService;
    }

    @Transactional
    public R checkin() {
        Long userId = UserContext.getUserId();
        LocalDate today = LocalDate.now();

        // Check if already checked in today
        LambdaQueryWrapper<Checkin> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(Checkin::getUserId, userId)
               .eq(Checkin::getCheckinDate, today);
        if (checkinRepository.selectCount(wrapper) > 0) {
            return R.error(BizCodeEnum.ALREADY_CHECKED_IN);
        }

        User user = userRepository.selectById(userId);
        if (user == null) {
            return R.error(BizCodeEnum.USER_NOT_FOUND);
        }

        // Calculate streak
        int streakDay = calculateStreak(user, today);
        long reward = BASE_REWARD + (long) streakDay * STREAK_BONUS;

        // Create checkin record
        Checkin checkin = new Checkin();
        checkin.setUserId(userId);
        checkin.setCheckinDate(today);
        checkin.setGoldReward(reward);
        checkin.setStreakDay(streakDay);
        checkin.setCreatedAt(LocalDateTime.now());
        checkinRepository.insert(checkin);

        // Update user
        user.setCheckinStreak(streakDay);
        user.setLastCheckin(today);
        user.setUpdatedAt(LocalDateTime.now());
        userRepository.updateById(user);

        // Add gold
        userService.addGold(userId, reward, "checkin",
                "Daily checkin - Day " + streakDay);

        // Check achievements
        achievementService.checkAndUnlock(userId);

        CheckinResponse response = CheckinResponse.builder()
                .goldReward(reward)
                .streakDay(streakDay)
                .totalGold(user.getGoldBalance() + reward)
                .build();

        return R.ok("checkin successful", response);
    }

    public R getTodayStatus() {
        Long userId = UserContext.getUserId();
        LocalDate today = LocalDate.now();

        LambdaQueryWrapper<Checkin> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(Checkin::getUserId, userId)
               .eq(Checkin::getCheckinDate, today);

        boolean checkedIn = checkinRepository.selectCount(wrapper) > 0;
        User user = userRepository.selectById(userId);

        return R.ok(new CheckinStatus(checkedIn, user != null ? user.getCheckinStreak() : 0));
    }

    private int calculateStreak(User user, LocalDate today) {
        LocalDate lastCheckin = user.getLastCheckin();
        if (lastCheckin == null) {
            return 1;
        }
        // Check if last checkin was yesterday
        if (lastCheckin.equals(today.minusDays(1))) {
            int nextStreak = user.getCheckinStreak() + 1;
            return Math.min(nextStreak, MAX_STREAK);
        }
        // Streak broken
        return 1;
    }

    // Inner class for status response
    @lombok.Data
    @lombok.AllArgsConstructor
    private static class CheckinStatus {
        private boolean checkedIn;
        private int currentStreak;
    }
}
