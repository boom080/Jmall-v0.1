package com.jmall.service;

import com.jmall.common.R;
import com.jmall.common.UserContext;
import com.jmall.entity.GoldLedger;
import com.jmall.entity.User;
import com.jmall.repository.GoldLedgerRepository;
import com.jmall.repository.UserRepository;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockedStatic;
import org.mockito.junit.jupiter.MockitoExtension;

import java.time.LocalDate;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class UserServiceTest {

    @Mock
    private UserRepository userRepository;

    @Mock
    private GoldLedgerRepository goldLedgerRepository;

    @InjectMocks
    private UserService userService;

    private MockedStatic<UserContext> userContextMock;

    private static final Long TEST_USER_ID = 1L;

    @BeforeEach
    void setUp() {
        userContextMock = mockStatic(UserContext.class);
        userContextMock.when(UserContext::getUserId).thenReturn(TEST_USER_ID);
    }

    @AfterEach
    void tearDown() {
        userContextMock.close();
    }

    // ---- addGold ----

    @Test
    void addGold_increasesBalanceAndCreatesLedger() {
        User user = createUser(10000L);
        when(userRepository.selectById(TEST_USER_ID)).thenReturn(user);

        userService.addGold(TEST_USER_ID, 500L, "checkin", "签到奖励");

        assertEquals(10500L, user.getGoldBalance());
        verify(userRepository).updateById(user);

        ArgumentCaptor<GoldLedger> captor = ArgumentCaptor.forClass(GoldLedger.class);
        verify(goldLedgerRepository).insert(captor.capture());
        GoldLedger ledger = captor.getValue();
        assertEquals(TEST_USER_ID, ledger.getUserId());
        assertEquals(500L, ledger.getAmount());
        assertEquals("checkin", ledger.getType());
        assertEquals("签到奖励", ledger.getDescription());
    }

    @Test
    void addGold_doesNothingWhenUserNotFound() {
        when(userRepository.selectById(TEST_USER_ID)).thenReturn(null);

        userService.addGold(TEST_USER_ID, 500L, "checkin", "test");

        verify(userRepository, never()).updateById(any(User.class));
        verify(goldLedgerRepository, never()).insert(any(GoldLedger.class));
    }

    @Test
    void deductGold_decreasesBalanceWhenSufficient() {
        User user = createUser(10000L);
        when(userRepository.selectById(TEST_USER_ID)).thenReturn(user);

        boolean result = userService.deductGold(TEST_USER_ID, 3000L, "purchase", "购买商品");

        assertTrue(result);
        assertEquals(7000L, user.getGoldBalance());
        verify(userRepository).updateById(user);

        ArgumentCaptor<GoldLedger> captor = ArgumentCaptor.forClass(GoldLedger.class);
        verify(goldLedgerRepository).insert(captor.capture());
        assertEquals(-3000L, captor.getValue().getAmount());
    }

    @Test
    void deductGold_returnsFalseWhenInsufficientFunds() {
        User user = createUser(100L);
        when(userRepository.selectById(TEST_USER_ID)).thenReturn(user);

        boolean result = userService.deductGold(TEST_USER_ID, 500L, "purchase", "test");

        assertFalse(result);
        assertEquals(100L, user.getGoldBalance()); // Unchanged
        verify(userRepository, never()).updateById(any(User.class));
        verify(goldLedgerRepository, never()).insert(any(GoldLedger.class));
    }

    @Test
    void deductGold_returnsFalseWhenUserNotFound() {
        when(userRepository.selectById(TEST_USER_ID)).thenReturn(null);

        boolean result = userService.deductGold(TEST_USER_ID, 500L, "purchase", "test");

        assertFalse(result);
    }

    @Test
    void deductGold_returnsFalseWhenExactBalance() {
        // Edge case: balance equals amount — still valid (should succeed)
        User user = createUser(500L);
        when(userRepository.selectById(TEST_USER_ID)).thenReturn(user);

        boolean result = userService.deductGold(TEST_USER_ID, 500L, "purchase", "test");

        assertTrue(result);
        assertEquals(0L, user.getGoldBalance());
    }

    // ---- addPoints ----

    @Test
    void addPoints_increasesPointsBalance() {
        User user = createUser(10000L);
        user.setPointsBalance(100L);
        when(userRepository.selectById(TEST_USER_ID)).thenReturn(user);

        userService.addPoints(TEST_USER_ID, 50L);

        assertEquals(150L, user.getPointsBalance());
        verify(userRepository).updateById(user);
    }

    // ---- getProfile ----

    @Test
    void getProfile_returnsUserProfile() {
        User user = createUser(10000L);
        user.setNickname("测试用户");
        when(userRepository.selectById(TEST_USER_ID)).thenReturn(user);

        R result = userService.getProfile();

        assertNotNull(result);
        assertEquals(10000, result.getCode()); // SUCCESS
        assertNotNull(result.getData());
    }

    @Test
    void getProfile_returnsErrorWhenUserNotFound() {
        when(userRepository.selectById(TEST_USER_ID)).thenReturn(null);

        R result = userService.getProfile();

        assertNotEquals(0, result.getCode());
    }

    // ---- getGoldBalance ----

    @Test
    void getGoldBalance_returnsBalance() {
        User user = createUser(9999L);
        when(userRepository.selectById(TEST_USER_ID)).thenReturn(user);

        R result = userService.getGoldBalance();
        assertEquals(10000, result.getCode());
    }

    // ---- Helpers ----

    private User createUser(Long goldBalance) {
        User user = new User();
        user.setId(TEST_USER_ID);
        user.setUsername("testuser");
        user.setPasswordHash("hashed");
        user.setNickname("测试");
        user.setRole("user");
        user.setGoldBalance(goldBalance);
        user.setPointsBalance(0L);
        user.setCheckinStreak(0);
        user.setLastCheckin(LocalDate.now().minusDays(1));
        return user;
    }
}
