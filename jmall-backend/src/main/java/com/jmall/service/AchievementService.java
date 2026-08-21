package com.jmall.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.jmall.common.R;
import com.jmall.common.UserContext;
import com.jmall.entity.Achievement;
import com.jmall.entity.Store;
import com.jmall.entity.Transaction;
import com.jmall.entity.User;
import com.jmall.entity.UserCollection;
import com.jmall.repository.AchievementRepository;
import com.jmall.repository.StoreRepository;
import com.jmall.repository.TransactionRepository;
import com.jmall.repository.UserCollectionRepository;
import com.jmall.repository.UserRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.*;
import java.util.stream.Collectors;

@Service
public class AchievementService {

    private final AchievementRepository achievementRepository;
    private final TransactionRepository transactionRepository;
    private final UserRepository userRepository;
    private final UserCollectionRepository collectionRepository;
    private final StoreRepository storeRepository;
    private final UserService userService;

    // Predefined achievements
    public enum AchievementDef {
        FIRST_PURCHASE("FIRST_PURCHASE", "First Purchase", "Make your first purchase", 100L),
        COLLECTOR_10("COLLECTOR_10", "Collector", "Collect 10 items", 500L),
        BIG_SPENDER_100K("BIG_SPENDER_100K", "Big Spender", "Spend over 100,000 gold in total", 2000L),
        STREAK_7("STREAK_7", "Weekly Warrior", "Maintain a 7-day checkin streak", 1000L),
        SHOP_OWNER("SHOP_OWNER", "Shop Owner", "Create your own store", 500L),
        SALE_10("SALE_10", "Hot Seller", "Sell 10 items from your store", 800L),
        NIGHT_OWL("NIGHT_OWL", "Night Owl", "Make a purchase between midnight and 5 AM", 300L),
        WHALE("WHALE", "Whale", "Earn over 1,000,000 gold from a single purchase", 5000L);

        private final String key;
        private final String name;
        private final String description;
        private final long goldBonus;

        AchievementDef(String key, String name, String description, long goldBonus) {
            this.key = key;
            this.name = name;
            this.description = description;
            this.goldBonus = goldBonus;
        }

        public String getKey() { return key; }
        public String getName() { return name; }
        public String getDescription() { return description; }
        public long getGoldBonus() { return goldBonus; }
    }

    public AchievementService(AchievementRepository achievementRepository,
                              TransactionRepository transactionRepository,
                              UserRepository userRepository,
                              UserCollectionRepository collectionRepository,
                              StoreRepository storeRepository,
                              UserService userService) {
        this.achievementRepository = achievementRepository;
        this.transactionRepository = transactionRepository;
        this.userRepository = userRepository;
        this.collectionRepository = collectionRepository;
        this.storeRepository = storeRepository;
        this.userService = userService;
    }

    @Transactional
    public void checkAndUnlock(Long userId) {
        Set<String> existingKeys = getUnlockedKeys(userId);

        // Check FIRST_PURCHASE
        if (!existingKeys.contains(AchievementDef.FIRST_PURCHASE.getKey())) {
            LambdaQueryWrapper<Transaction> txnWrapper = new LambdaQueryWrapper<>();
            txnWrapper.eq(Transaction::getBuyerId, userId);
            if (transactionRepository.selectCount(txnWrapper) > 0) {
                unlockAchievement(userId, AchievementDef.FIRST_PURCHASE);
            }
        }

        // Check COLLECTOR_10 — count UserCollection records (favorited items)
        if (!existingKeys.contains(AchievementDef.COLLECTOR_10.getKey())) {
            LambdaQueryWrapper<UserCollection> colWrapper = new LambdaQueryWrapper<>();
            colWrapper.eq(UserCollection::getUserId, userId);
            if (collectionRepository.selectCount(colWrapper) >= 10) {
                unlockAchievement(userId, AchievementDef.COLLECTOR_10);
            }
        }

        // Check BIG_SPENDER_100K
        if (!existingKeys.contains(AchievementDef.BIG_SPENDER_100K.getKey())) {
            Long totalSpent = getTotalSpent(userId);
            if (totalSpent >= 100000L) {
                unlockAchievement(userId, AchievementDef.BIG_SPENDER_100K);
            }
        }

        // Check STREAK_7
        if (!existingKeys.contains(AchievementDef.STREAK_7.getKey())) {
            User user = userRepository.selectById(userId);
            if (user != null && user.getCheckinStreak() >= 7) {
                unlockAchievement(userId, AchievementDef.STREAK_7);
            }
        }

        // Check SALE_10 — count transactions through the user's store
        if (!existingKeys.contains(AchievementDef.SALE_10.getKey())) {
            LambdaQueryWrapper<Store> storeWrapper = new LambdaQueryWrapper<>();
            storeWrapper.eq(Store::getUserId, userId);
            Store store = storeRepository.selectOne(storeWrapper);
            if (store != null) {
                LambdaQueryWrapper<Transaction> txnWrapper = new LambdaQueryWrapper<>();
                txnWrapper.eq(Transaction::getStoreId, store.getId());
                if (transactionRepository.selectCount(txnWrapper) >= 10) {
                    unlockAchievement(userId, AchievementDef.SALE_10);
                }
            }
        }

        // Check NIGHT_OWL — any purchase between 00:00~05:00
        if (!existingKeys.contains(AchievementDef.NIGHT_OWL.getKey())) {
            LambdaQueryWrapper<Transaction> txnWrapper = new LambdaQueryWrapper<>();
            txnWrapper.eq(Transaction::getBuyerId, userId);
            List<Transaction> txns = transactionRepository.selectList(txnWrapper);
            boolean hasNightPurchase = txns.stream().anyMatch(t -> {
                int hour = t.getCreatedAt().getHour();
                return hour >= 0 && hour < 5;
            });
            if (hasNightPurchase) {
                unlockAchievement(userId, AchievementDef.NIGHT_OWL);
            }
        }

        // Check WHALE — single purchase earned >= 1,000,000 gold
        if (!existingKeys.contains(AchievementDef.WHALE.getKey())) {
            LambdaQueryWrapper<Transaction> txnWrapper = new LambdaQueryWrapper<>();
            txnWrapper.eq(Transaction::getBuyerId, userId);
            List<Transaction> txns = transactionRepository.selectList(txnWrapper);
            boolean hasWhalePurchase = txns.stream().anyMatch(t -> t.getGoldEarned() >= 1_000_000L);
            if (hasWhalePurchase) {
                unlockAchievement(userId, AchievementDef.WHALE);
            }
        }
    }

    @Transactional
    public void checkShopOwner(Long userId) {
        Set<String> existingKeys = getUnlockedKeys(userId);
        if (!existingKeys.contains(AchievementDef.SHOP_OWNER.getKey())) {
            unlockAchievement(userId, AchievementDef.SHOP_OWNER);
        }
    }

    private void unlockAchievement(Long userId, AchievementDef def) {
        Achievement achievement = new Achievement();
        achievement.setUserId(userId);
        achievement.setAchievementKey(def.getKey());
        achievement.setUnlockedAt(LocalDateTime.now());
        achievementRepository.insert(achievement);

        // Award gold bonus
        if (def.getGoldBonus() > 0) {
            userService.addGold(userId, def.getGoldBonus(), "bonus",
                    "Achievement unlocked: " + def.getName());
        }
    }

    private Set<String> getUnlockedKeys(Long userId) {
        LambdaQueryWrapper<Achievement> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(Achievement::getUserId, userId);
        List<Achievement> achievements = achievementRepository.selectList(wrapper);
        return achievements.stream()
                .map(Achievement::getAchievementKey)
                .collect(Collectors.toSet());
    }

    public R getUnlocked() {
        Long userId = UserContext.getUserId();
        List<Achievement> achievements = achievementRepository.selectList(
                new LambdaQueryWrapper<Achievement>().eq(Achievement::getUserId, userId));

        List<Map<String, Object>> result = new ArrayList<>();
        Set<String> unlockedKeys = achievements.stream()
                .map(Achievement::getAchievementKey)
                .collect(Collectors.toSet());

        for (AchievementDef def : AchievementDef.values()) {
            Map<String, Object> entry = new HashMap<>();
            entry.put("key", def.getKey());
            entry.put("name", def.getName());
            entry.put("description", def.getDescription());
            entry.put("goldBonus", def.getGoldBonus());
            entry.put("unlocked", unlockedKeys.contains(def.getKey()));
            result.add(entry);
        }

        return R.ok(result);
    }

    private Long getTotalSpent(Long userId) {
        LambdaQueryWrapper<Transaction> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(Transaction::getBuyerId, userId);
        List<Transaction> transactions = transactionRepository.selectList(wrapper);
        return transactions.stream()
                .mapToLong(Transaction::getAmount)
                .sum();
    }
}
