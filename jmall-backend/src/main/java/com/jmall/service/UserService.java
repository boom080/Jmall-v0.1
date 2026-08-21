package com.jmall.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.jmall.common.BizCodeEnum;
import com.jmall.common.R;
import com.jmall.common.UserContext;
import com.jmall.dto.UserProfileResponse;
import com.jmall.entity.GoldLedger;
import com.jmall.entity.User;
import com.jmall.repository.GoldLedgerRepository;
import com.jmall.repository.UserRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;

@Service
public class UserService {

    private final UserRepository userRepository;
    private final GoldLedgerRepository goldLedgerRepository;

    public UserService(UserRepository userRepository, GoldLedgerRepository goldLedgerRepository) {
        this.userRepository = userRepository;
        this.goldLedgerRepository = goldLedgerRepository;
    }

    public R getProfile() {
        Long userId = UserContext.getUserId();
        User user = userRepository.selectById(userId);
        if (user == null) {
            return R.error(BizCodeEnum.USER_NOT_FOUND);
        }

        UserProfileResponse profile = UserProfileResponse.builder()
                .id(user.getId())
                .username(user.getUsername())
                .nickname(user.getNickname())
                .goldBalance(user.getGoldBalance())
                .pointsBalance(user.getPointsBalance())
                .checkinStreak(user.getCheckinStreak())
                .role(user.getRole())
                .build();

        return R.ok(profile);
    }

    public R getGoldBalance() {
        Long userId = UserContext.getUserId();
        User user = userRepository.selectById(userId);
        if (user == null) {
            return R.error(BizCodeEnum.USER_NOT_FOUND);
        }
        return R.ok(user.getGoldBalance());
    }

    @Transactional
    public void addGold(Long userId, Long amount, String type, String description) {
        User user = userRepository.selectById(userId);
        if (user != null) {
            user.setGoldBalance(user.getGoldBalance() + amount);
            user.setUpdatedAt(LocalDateTime.now());
            userRepository.updateById(user);

            GoldLedger ledger = new GoldLedger();
            ledger.setUserId(userId);
            ledger.setAmount(amount);
            ledger.setType(type);
            ledger.setDescription(description);
            ledger.setCreatedAt(LocalDateTime.now());
            goldLedgerRepository.insert(ledger);
        }
    }

    @Transactional
    public boolean deductGold(Long userId, Long amount, String type, String description) {
        User user = userRepository.selectById(userId);
        if (user == null || user.getGoldBalance() < amount) {
            return false;
        }
        user.setGoldBalance(user.getGoldBalance() - amount);
        user.setUpdatedAt(LocalDateTime.now());
        userRepository.updateById(user);

        GoldLedger ledger = new GoldLedger();
        ledger.setUserId(userId);
        ledger.setAmount(-amount);
        ledger.setType(type);
        ledger.setDescription(description);
        ledger.setCreatedAt(LocalDateTime.now());
        goldLedgerRepository.insert(ledger);
        return true;
    }

    @Transactional
    public void addPoints(Long userId, Long points) {
        User user = userRepository.selectById(userId);
        if (user != null) {
            user.setPointsBalance(user.getPointsBalance() + points);
            user.setUpdatedAt(LocalDateTime.now());
            userRepository.updateById(user);
        }
    }

    public R getGoldLedger() {
        Long userId = UserContext.getUserId();
        LambdaQueryWrapper<GoldLedger> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(GoldLedger::getUserId, userId)
               .orderByDesc(GoldLedger::getCreatedAt)
               .last("LIMIT 50");
        List<GoldLedger> ledgers = goldLedgerRepository.selectList(wrapper);
        return R.ok(ledgers);
    }
}
