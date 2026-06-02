package com.shf.gulimall.product.app.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.shf.gulimall.product.app.dto.CurrentUserProfile;
import com.shf.gulimall.product.app.dto.UserAddressResponse;
import com.shf.gulimall.product.app.dto.UserOrderCreateRequest;
import com.shf.gulimall.product.dao.UserOrderDao;
import com.shf.gulimall.product.dao.UserOrderItemDao;
import com.shf.gulimall.product.entity.SkuInfoEntity;
import com.shf.gulimall.product.entity.UserOrderEntity;
import com.shf.gulimall.product.service.CategoryService;
import com.shf.gulimall.product.service.SkuInfoService;
import org.junit.Before;
import org.junit.Test;
import org.mockito.ArgumentCaptor;
import org.springframework.data.redis.core.HashOperations;
import org.springframework.data.redis.core.StringRedisTemplate;

import java.math.BigDecimal;
import java.util.Date;
import java.util.LinkedHashMap;
import java.util.Map;

import static org.junit.Assert.assertEquals;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.doAnswer;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

public class UserCommerceApplicationServiceTests {

    private StringRedisTemplate stringRedisTemplate;
    private HashOperations<String, Object, Object> hashOperations;
    private SkuInfoService skuInfoService;
    private CategoryService categoryService;
    private UserOrderDao userOrderDao;
    private UserOrderItemDao userOrderItemDao;
    private CurrentUserResolver currentUserResolver;
    private UserAddressApplicationService userAddressApplicationService;
    private com.shf.gulimall.product.feign.OrderUserFeignService orderUserFeignService;
    private UserCommerceApplicationService service;

    @Before
    public void setUp() throws Exception {
        stringRedisTemplate = mock(StringRedisTemplate.class);
        hashOperations = mock(HashOperations.class);
        skuInfoService = mock(SkuInfoService.class);
        categoryService = mock(CategoryService.class);
        userOrderDao = mock(UserOrderDao.class);
        userOrderItemDao = mock(UserOrderItemDao.class);
        currentUserResolver = mock(CurrentUserResolver.class);
        userAddressApplicationService = mock(UserAddressApplicationService.class);
        orderUserFeignService = mock(com.shf.gulimall.product.feign.OrderUserFeignService.class);

        when(stringRedisTemplate.opsForHash()).thenReturn(hashOperations);

        CurrentUserProfile user = new CurrentUserProfile();
        user.setUserId(101L);
        user.setUsername("alice");
        user.setDisplayName("Alice");
        when(currentUserResolver.requireCurrentUser()).thenReturn(user);

        UserAddressResponse address = new UserAddressResponse();
        address.setId(5L);
        address.setName("Alice");
        address.setPhone("13800000000");
        address.setProvince("Shanghai");
        address.setCity("Pudong");
        address.setRegion("Zhangjiang");
        address.setDetailAddress("Road 1");
        when(userAddressApplicationService.getAddressForCurrentUser(5L)).thenReturn(address);

        Map<String, Object> cart = new LinkedHashMap<String, Object>();
        cart.put("skuId", 14);
        cart.put("title", "Jrun Phone 14");
        cart.put("category", "手机数码");
        cart.put("price", 1999);
        cart.put("quantity", 1);
        cart.put("coverUrl", "");
        cart.put("summary", "轻旗舰手机");
        cart.put("totalAmount", 1999);
        when(hashOperations.values("jrunmall:user:cart:101")).thenReturn(java.util.Collections.<Object>singletonList(new com.fasterxml.jackson.databind.ObjectMapper().writeValueAsString(cart)));

        SkuInfoEntity skuInfo = new SkuInfoEntity();
        skuInfo.setSkuId(14L);
        skuInfo.setSpuId(1001L);
        skuInfo.setPrice(new BigDecimal("1999.00"));
        when(skuInfoService.getById(14L)).thenReturn(skuInfo);

        doAnswer((invocation) -> {
            UserOrderEntity entity = invocation.getArgument(0);
            entity.setId(1L);
            entity.setCreatedTime(entity.getCreatedTime() == null ? new Date() : entity.getCreatedTime());
            return 1;
        }).when(userOrderDao).insert(any(UserOrderEntity.class));
        when(userOrderDao.selectById(1L)).thenAnswer((invocation) -> {
            UserOrderEntity entity = new UserOrderEntity();
            entity.setId(1L);
            entity.setOrderSn("ORDER-1");
            entity.setUserId(101L);
            entity.setUsername("alice");
            entity.setStatus("CREATED");
            entity.setTotalAmount(new BigDecimal("1999.00"));
            entity.setTotalQuantity(1);
            entity.setOrderSource("normal");
            entity.setAddressId(5L);
            entity.setReceiverName("Alice");
            entity.setReceiverPhone("13800000000");
            entity.setReceiverAddress("ShanghaiPudongZhangjiangRoad 1");
            entity.setCreatedTime(new Date());
            return entity;
        });
        when(userOrderItemDao.selectList(any(QueryWrapper.class))).thenReturn(java.util.Collections.emptyList());

        service = new UserCommerceApplicationService(
                stringRedisTemplate,
                skuInfoService,
                categoryService,
                userOrderDao,
                userOrderItemDao,
                currentUserResolver,
                userAddressApplicationService,
                orderUserFeignService
        );
    }

    @Test
    public void createOrderWritesAddressSnapshot() {
        UserOrderCreateRequest request = new UserOrderCreateRequest();
        request.setAddressId(5L);
        request.setNote("demo");

        service.createOrder(request);

        ArgumentCaptor<UserOrderEntity> captor = ArgumentCaptor.forClass(UserOrderEntity.class);
        org.mockito.Mockito.verify(userOrderDao).insert(captor.capture());
        UserOrderEntity saved = captor.getValue();
        assertEquals(Long.valueOf(5L), saved.getAddressId());
        assertEquals("Alice", saved.getReceiverName());
        assertEquals("13800000000", saved.getReceiverPhone());
        assertEquals("ShanghaiPudongZhangjiangRoad 1", saved.getReceiverAddress());
    }
}





