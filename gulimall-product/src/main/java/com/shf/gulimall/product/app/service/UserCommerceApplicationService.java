package com.shf.gulimall.product.app.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.shf.common.utils.R;
import com.shf.gulimall.product.app.dto.CurrentUserProfile;
import com.shf.gulimall.product.app.dto.MerchantOrderSummaryResponse;
import com.shf.gulimall.product.app.dto.SeckillOrderEvent;
import com.shf.gulimall.product.app.dto.UserAddressResponse;
import com.shf.gulimall.product.app.dto.UserCartItemResponse;
import com.shf.gulimall.product.app.dto.UserCartItemUpdateRequest;
import com.shf.gulimall.product.app.dto.UserCartItemUpsertRequest;
import com.shf.gulimall.product.app.dto.UserCartResponse;
import com.shf.gulimall.product.app.dto.UserOrderCreateRequest;
import com.shf.gulimall.product.app.dto.UserOrderItemResponse;
import com.shf.gulimall.product.app.dto.UserOrderResponse;
import com.shf.gulimall.product.dao.UserOrderDao;
import com.shf.gulimall.product.dao.UserOrderItemDao;
import com.shf.gulimall.product.entity.CategoryEntity;
import com.shf.gulimall.product.entity.SkuInfoEntity;
import com.shf.gulimall.product.entity.UserOrderEntity;
import com.shf.gulimall.product.entity.UserOrderItemEntity;
import com.shf.gulimall.product.feign.OrderUserFeignService;
import com.shf.gulimall.product.service.CategoryService;
import com.shf.gulimall.product.service.SkuInfoService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.redis.core.HashOperations;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.Date;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.LinkedHashMap;
import java.util.Random;
import java.util.TimeZone;

@Service
public class UserCommerceApplicationService {

    private static final Logger log = LoggerFactory.getLogger(UserCommerceApplicationService.class);

    private static final String STATUS_CREATED = "CREATED";
    private static final String STATUS_PAID = "PAID";
    private static final String SOURCE_NORMAL = "normal";
    private static final String SOURCE_SECKILL = "seckill";

    private final StringRedisTemplate stringRedisTemplate;
    private final SkuInfoService skuInfoService;
    private final CategoryService categoryService;
    private final UserOrderDao userOrderDao;
    private final UserOrderItemDao userOrderItemDao;
    private final CurrentUserResolver currentUserResolver;
    private final UserAddressApplicationService userAddressApplicationService;
    private final OrderUserFeignService orderUserFeignService;
    private final ObjectMapper objectMapper;

    public UserCommerceApplicationService(StringRedisTemplate stringRedisTemplate,
                                          SkuInfoService skuInfoService,
                                          CategoryService categoryService,
                                          UserOrderDao userOrderDao,
                                          UserOrderItemDao userOrderItemDao,
                                          CurrentUserResolver currentUserResolver,
                                          UserAddressApplicationService userAddressApplicationService,
                                          OrderUserFeignService orderUserFeignService) {
        this.stringRedisTemplate = stringRedisTemplate;
        this.skuInfoService = skuInfoService;
        this.categoryService = categoryService;
        this.userOrderDao = userOrderDao;
        this.userOrderItemDao = userOrderItemDao;
        this.currentUserResolver = currentUserResolver;
        this.userAddressApplicationService = userAddressApplicationService;
        this.orderUserFeignService = orderUserFeignService;
        this.objectMapper = new ObjectMapper();
    }

    public UserCartResponse getCart() {
        CurrentUserProfile user = currentUserResolver.requireCurrentUser();
        List<UserCartItemResponse> items = loadCartItems(user.getUserId());
        return buildCartResponse(items, user);
    }

    public UserCartResponse addCartItem(UserCartItemUpsertRequest request) {
        CurrentUserProfile user = currentUserResolver.requireCurrentUser();
        validateSkuId(request.getSkuId());
        validateQuantity(request.getQuantity());

        List<UserCartItemResponse> items = loadCartItems(user.getUserId());
        UserCartItemResponse existing = findCartItem(items, request.getSkuId());
        if (existing == null) {
            items.add(buildCartItem(request.getSkuId(), request.getQuantity()));
        } else {
            existing.setQuantity(existing.getQuantity() + request.getQuantity());
            existing.setTotalAmount(calculateLineAmount(existing.getPrice(), existing.getQuantity()));
        }
        saveCartItems(user.getUserId(), items);
        return buildCartResponse(items, user);
    }

    public UserCartResponse updateCartItem(Long skuId, UserCartItemUpdateRequest request) {
        CurrentUserProfile user = currentUserResolver.requireCurrentUser();
        validateSkuId(skuId);
        validateQuantity(request.getQuantity());

        List<UserCartItemResponse> items = loadCartItems(user.getUserId());
        UserCartItemResponse existing = findCartItem(items, skuId);
        if (existing == null) {
            throw new IllegalArgumentException("购物车中不存在该商品");
        }

        existing.setQuantity(request.getQuantity());
        existing.setTotalAmount(calculateLineAmount(existing.getPrice(), existing.getQuantity()));
        saveCartItems(user.getUserId(), items);
        return buildCartResponse(items, user);
    }

    public UserCartResponse deleteCartItem(Long skuId) {
        CurrentUserProfile user = currentUserResolver.requireCurrentUser();
        validateSkuId(skuId);

        List<UserCartItemResponse> items = loadCartItems(user.getUserId());
        UserCartItemResponse existing = findCartItem(items, skuId);
        if (existing == null) {
            throw new IllegalArgumentException("购物车中不存在该商品");
        }

        items.remove(existing);
        saveCartItems(user.getUserId(), items);
        return buildCartResponse(items, user);
    }

    public UserOrderResponse createOrder(UserOrderCreateRequest request) {
        CurrentUserProfile user = currentUserResolver.requireCurrentUser();
        List<UserCartItemResponse> items = loadCartItems(user.getUserId());
        if (items.isEmpty()) {
            throw new IllegalArgumentException("购物车为空，无法创建订单");
        }
        if (request == null || request.getAddressId() == null || request.getAddressId() <= 0) {
            throw new IllegalArgumentException("请选择收货地址");
        }

        UserAddressResponse address = userAddressApplicationService.getAddressForCurrentUser(request.getAddressId());
        Date now = new Date();

        UserOrderEntity order = new UserOrderEntity();
        order.setOrderSn(generateOrderSn(now));
        order.setUserId(user.getUserId());
        order.setUsername(firstNonBlank(user.getUsername(), user.getDisplayName(), "jrunmall-user"));
        order.setStatus(STATUS_CREATED);
        order.setTotalAmount(sumAmount(items));
        order.setTotalQuantity(sumQuantity(items));
        order.setNote(normalizeNote(request.getNote()));
        order.setOrderSource(SOURCE_NORMAL);
        order.setBizToken(null);
        order.setAddressId(address.getId());
        order.setReceiverName(address.getName());
        order.setReceiverPhone(address.getPhone());
        order.setReceiverAddress(joinAddress(address));
        order.setCreatedTime(now);
        order.setUpdatedTime(now);
        userOrderDao.insert(order);

        for (UserCartItemResponse item : items) {
            UserOrderItemEntity orderItem = new UserOrderItemEntity();
            orderItem.setOrderId(order.getId());
            orderItem.setOrderSn(order.getOrderSn());
            orderItem.setSkuId(item.getSkuId());
            SkuInfoEntity skuInfo = skuInfoService.getById(item.getSkuId());
            orderItem.setSpuId(skuInfo == null ? null : skuInfo.getSpuId());
            orderItem.setTitle(item.getTitle());
            orderItem.setCategory(item.getCategory());
            orderItem.setCoverUrl(item.getCoverUrl());
            orderItem.setSummary(item.getSummary());
            orderItem.setPrice(defaultBigDecimal(item.getPrice()));
            orderItem.setQuantity(item.getQuantity());
            orderItem.setLineAmount(calculateLineAmount(item.getPrice(), item.getQuantity()));
            orderItem.setCreatedTime(now);
            userOrderItemDao.insert(orderItem);
        }

        saveCartItems(user.getUserId(), Collections.<UserCartItemResponse>emptyList());
        return getOrder(order.getId());
    }

    public UserOrderResponse createSeckillOrder(SeckillOrderEvent event) {
        validateSeckillEvent(event);
        UserOrderEntity existing = userOrderDao.selectOne(new QueryWrapper<UserOrderEntity>()
                .eq("biz_token", event.getOrderToken()));
        if (existing != null) {
            return toOrderResponse(existing);
        }

        Date now = event.getTimestamp() == null ? new Date() : event.getTimestamp();
        SkuInfoEntity skuInfo = skuInfoService.getById(event.getSkuId());
        if (skuInfo == null) {
            throw new IllegalArgumentException("秒杀商品不存在");
        }

        UserOrderEntity order = new UserOrderEntity();
        order.setOrderSn(generateSeckillOrderSn(now, event.getOrderToken()));
        order.setUserId(event.getUserId());
        order.setUsername(resolveSeckillUsername(event.getUserId()));
        order.setStatus(STATUS_CREATED);
        order.setTotalAmount(calculateLineAmount(defaultBigDecimal(skuInfo.getPrice()), event.getQuantity()));
        order.setTotalQuantity(event.getQuantity());
        order.setNote("秒杀订单");
        order.setOrderSource(SOURCE_SECKILL);
        order.setBizToken(event.getOrderToken());
        order.setCreatedTime(now);
        order.setUpdatedTime(now);
        userOrderDao.insert(order);

        UserOrderItemEntity orderItem = new UserOrderItemEntity();
        orderItem.setOrderId(order.getId());
        orderItem.setOrderSn(order.getOrderSn());
        orderItem.setSkuId(event.getSkuId());
        orderItem.setSpuId(skuInfo.getSpuId());
        orderItem.setTitle(firstNonBlank(skuInfo.getSkuTitle(), skuInfo.getSkuName(), "秒杀商品"));
        orderItem.setCategory(resolveCategoryName(skuInfo.getCatalogId()));
        orderItem.setCoverUrl(firstNonBlank(skuInfo.getSkuDefaultImg(), ""));
        orderItem.setSummary(firstNonBlank(skuInfo.getSkuSubtitle(), skuInfo.getSkuDesc(), "Jrunmall 秒杀商品"));
        orderItem.setPrice(defaultBigDecimal(skuInfo.getPrice()));
        orderItem.setQuantity(event.getQuantity());
        orderItem.setLineAmount(calculateLineAmount(skuInfo.getPrice(), event.getQuantity()));
        orderItem.setCreatedTime(now);
        userOrderItemDao.insert(orderItem);

        return toOrderResponse(order);
    }

    public UserOrderResponse confirmOrderAddress(Long orderId, UserOrderCreateRequest request) {
        CurrentUserProfile user = currentUserResolver.requireCurrentUser();
        validateOrderId(orderId);
        if (request == null || request.getAddressId() == null || request.getAddressId() <= 0) {
            throw new IllegalArgumentException("请选择收货地址");
        }
        UserOrderEntity order = userOrderDao.selectById(orderId);
        if (order == null || !user.getUserId().equals(order.getUserId())) {
            throw new IllegalArgumentException("订单不存在");
        }
        if (!STATUS_CREATED.equals(order.getStatus())) {
            throw new IllegalArgumentException("当前订单状态不能修改地址");
        }

        UserAddressResponse address = userAddressApplicationService.getAddressForCurrentUser(request.getAddressId());
        order.setAddressId(address.getId());
        order.setReceiverName(address.getName());
        order.setReceiverPhone(address.getPhone());
        order.setReceiverAddress(joinAddress(address));
        order.setNote(normalizeNote(request.getNote()));
        order.setUpdatedTime(new Date());
        userOrderDao.updateById(order);
        return toOrderResponse(order);
    }

    public List<UserOrderResponse> listOrders() {
        CurrentUserProfile user = currentUserResolver.requireCurrentUser();
        List<UserOrderEntity> orders = userOrderDao.selectList(new QueryWrapper<UserOrderEntity>()
                .eq("user_id", user.getUserId())
                .orderByDesc("created_time"));

        List<UserOrderResponse> responses = new ArrayList<UserOrderResponse>();
        for (UserOrderEntity order : orders) {
            responses.add(toOrderResponse(order));
        }
        return responses;
    }

    public List<UserOrderResponse> listAllOrders() {
        CurrentUserProfile user = currentUserResolver.requireCurrentUser();
        Map<Long, UserOrderResponse> orderById = new LinkedHashMap<Long, UserOrderResponse>();
        for (UserOrderResponse order : listOrders()) {
            if (order != null && order.getOrderId() != null) {
                orderById.put(order.getOrderId(), order);
            }
        }
        for (UserOrderResponse order : loadCurrentUserSeckillOrderResponses(user.getUserId())) {
            if (order != null && order.getOrderId() != null && !orderById.containsKey(order.getOrderId())) {
                orderById.put(order.getOrderId(), order);
            }
        }
        List<UserOrderResponse> orders = new ArrayList<UserOrderResponse>(orderById.values());
        orders.sort(new Comparator<UserOrderResponse>() {
            @Override
            public int compare(UserOrderResponse left, UserOrderResponse right) {
                long rightTime = right == null || right.getCreatedTime() == null ? 0L : right.getCreatedTime().getTime();
                long leftTime = left == null || left.getCreatedTime() == null ? 0L : left.getCreatedTime().getTime();
                return Long.compare(rightTime, leftTime);
            }
        });
        return orders;
    }

    public UserOrderResponse getOrderByRef(String orderRef) {
        CurrentUserProfile user = currentUserResolver.requireCurrentUser();
        if (orderRef == null || orderRef.trim().isEmpty()) {
            throw new IllegalArgumentException("orderRef 非法");
        }
        String normalized = orderRef.trim();
        if (normalized.startsWith(SOURCE_SECKILL + "-")) {
            Long orderId = parseOrderId(normalized.substring((SOURCE_SECKILL + "-").length()));
            return loadCurrentUserSeckillOrderDetail(user.getUserId(), orderId);
        }
        return getOrder(parseOrderId(normalized));
    }

    public UserOrderResponse getOrder(Long orderId) {
        CurrentUserProfile user = currentUserResolver.requireCurrentUser();
        validateOrderId(orderId);
        UserOrderEntity order = userOrderDao.selectById(orderId);
        if (order == null || !user.getUserId().equals(order.getUserId())) {
            return null;
        }
        return toOrderResponse(order);
    }

    public UserOrderResponse payOrder(Long orderId) {
        CurrentUserProfile user = currentUserResolver.requireCurrentUser();
        validateOrderId(orderId);
        UserOrderEntity order = userOrderDao.selectById(orderId);
        if (order == null || !user.getUserId().equals(order.getUserId())) {
            throw new IllegalArgumentException("订单不存在");
        }
        if (!STATUS_PAID.equals(order.getStatus())) {
            Date now = new Date();
            order.setStatus(STATUS_PAID);
            order.setPaymentTime(now);
            order.setUpdatedTime(now);
            userOrderDao.updateById(order);
        }
        return toOrderResponse(order);
    }

    public Object listCurrentUserSeckillOrders() {
        CurrentUserProfile user = currentUserResolver.requireCurrentUser();
        R response = orderUserFeignService.listUserSeckillOrders(user.getUserId());
        Object code = response.get("code");
        if (!(code instanceof Number) || ((Number) code).intValue() != 0) {
            throw new IllegalStateException(String.valueOf(response.get("msg")));
        }
        Object data = response.get("data");
        return data == null ? Collections.emptyList() : data;
    }

    public List<MerchantOrderSummaryResponse> listMerchantOrders() {
        List<UserOrderEntity> orders = userOrderDao.selectList(new QueryWrapper<UserOrderEntity>()
                .orderByDesc("created_time"));
        List<MerchantOrderSummaryResponse> responses = new ArrayList<MerchantOrderSummaryResponse>();
        for (UserOrderEntity order : orders) {
            MerchantOrderSummaryResponse response = new MerchantOrderSummaryResponse();
            response.setOrderId(order.getId());
            response.setOrderSn(order.getOrderSn());
            response.setUserId(order.getUserId());
            response.setUsername(order.getUsername());
            response.setStatus(order.getStatus());
            response.setTotalAmount(defaultBigDecimal(order.getTotalAmount()));
            response.setTotalQuantity(order.getTotalQuantity() == null ? 0 : order.getTotalQuantity());
            response.setCreatedTime(order.getCreatedTime());
            response.setPaymentTime(order.getPaymentTime());
            responses.add(response);
        }
        return responses;
    }

    private UserCartResponse buildCartResponse(List<UserCartItemResponse> items, CurrentUserProfile user) {
        items.sort(Comparator.comparing(UserCartItemResponse::getSkuId));
        UserCartResponse response = new UserCartResponse();
        response.setUserId(user.getUserId());
        response.setDisplayName(firstNonBlank(user.getDisplayName(), user.getUsername(), "Jrunmall User"));
        response.setItems(items);
        response.setTotalCount(sumQuantity(items));
        response.setTotalAmount(sumAmount(items));
        return response;
    }

    private UserCartItemResponse buildCartItem(Long skuId, Integer quantity) {
        SkuInfoEntity skuInfo = skuInfoService.getById(skuId);
        if (skuInfo == null) {
            throw new IllegalArgumentException("商品不存在");
        }

        UserCartItemResponse item = new UserCartItemResponse();
        item.setSkuId(skuId);
        item.setTitle(firstNonBlank(skuInfo.getSkuTitle(), skuInfo.getSkuName(), "未命名商品"));
        item.setCategory(resolveCategoryName(skuInfo.getCatalogId()));
        item.setPrice(defaultBigDecimal(skuInfo.getPrice()));
        item.setQuantity(quantity);
        item.setCoverUrl(firstNonBlank(skuInfo.getSkuDefaultImg(), ""));
        item.setSummary(firstNonBlank(skuInfo.getSkuSubtitle(), skuInfo.getSkuDesc(), "Jrunmall 商品"));
        item.setTotalAmount(calculateLineAmount(item.getPrice(), quantity));
        return item;
    }

    private String normalizeNote(String note) {
        if (note == null) {
            return "";
        }
        String trimmed = note.trim();
        if (trimmed.length() > 120) {
            throw new IllegalArgumentException("订单备注不能超过 120 个字符");
        }
        return trimmed;
    }

    private UserOrderResponse toOrderResponse(UserOrderEntity order) {
        UserOrderResponse response = new UserOrderResponse();
        response.setOrderId(order.getId());
        response.setOrderRef(String.valueOf(order.getId()));
        response.setOrderSn(order.getOrderSn());
        response.setUserId(order.getUserId());
        response.setUsername(order.getUsername());
        response.setStatus(order.getStatus());
        response.setTotalAmount(defaultBigDecimal(order.getTotalAmount()));
        response.setTotalQuantity(order.getTotalQuantity() == null ? 0 : order.getTotalQuantity());
        response.setNote(order.getNote());
        response.setOrderSource(firstNonBlank(order.getOrderSource(), SOURCE_NORMAL));
        response.setBizToken(order.getBizToken());
        response.setAddressId(order.getAddressId());
        response.setReceiverName(order.getReceiverName());
        response.setReceiverPhone(order.getReceiverPhone());
        response.setReceiverAddress(order.getReceiverAddress());
        response.setCreatedTime(order.getCreatedTime());
        response.setPaymentTime(order.getPaymentTime());

        List<UserOrderItemEntity> orderItems = userOrderItemDao.selectList(new QueryWrapper<UserOrderItemEntity>()
                .eq("order_id", order.getId())
                .orderByAsc("id"));
        List<UserOrderItemResponse> items = new ArrayList<UserOrderItemResponse>();
        for (UserOrderItemEntity orderItem : orderItems) {
            UserOrderItemResponse item = new UserOrderItemResponse();
            item.setSkuId(orderItem.getSkuId());
            item.setTitle(orderItem.getTitle());
            item.setCategory(orderItem.getCategory());
            item.setCoverUrl(orderItem.getCoverUrl());
            item.setSummary(orderItem.getSummary());
            item.setPrice(defaultBigDecimal(orderItem.getPrice()));
            item.setQuantity(orderItem.getQuantity() == null ? 0 : orderItem.getQuantity());
            item.setLineAmount(defaultBigDecimal(orderItem.getLineAmount()));
            items.add(item);
        }
        response.setItems(items);
        return response;
    }

    private List<UserOrderResponse> loadCurrentUserSeckillOrderResponses(Long userId) {
        try {
            R response = orderUserFeignService.listUserSeckillOrders(userId);
            Object code = response.get("code");
            if (!(code instanceof Number) || ((Number) code).intValue() != 0) {
                log.warn("Seckill order aggregation returned non-success response for userId={}: {}", userId, response.get("msg"));
                return Collections.emptyList();
            }
            Object data = response.get("data");
            if (data == null) {
                return Collections.emptyList();
            }
            List<SeckillOrderSummaryPayload> payloads = objectMapper.convertValue(data, new TypeReference<List<SeckillOrderSummaryPayload>>() { });
            List<UserOrderResponse> responses = new ArrayList<UserOrderResponse>();
            for (SeckillOrderSummaryPayload payload : payloads) {
                responses.add(mapSeckillSummary(payload));
            }
            return responses;
        } catch (RuntimeException ex) {
            log.warn("Seckill order aggregation skipped because jrunmall-order is unavailable, userId={}", userId, ex);
            return Collections.emptyList();
        }
    }

    private UserOrderResponse loadCurrentUserSeckillOrderDetail(Long userId, Long orderId) {
        R response;
        try {
            response = orderUserFeignService.getUserSeckillOrderDetail(userId, orderId);
        } catch (RuntimeException ex) {
            log.warn("Seckill order detail skipped because jrunmall-order is unavailable, userId={}, orderId={}", userId, orderId, ex);
            return null;
        }
        Object code = response.get("code");
        if (!(code instanceof Number) || ((Number) code).intValue() != 0) {
            return null;
        }
        Object data = response.get("data");
        if (data == null) {
            return null;
        }
        SeckillOrderDetailPayload payload = objectMapper.convertValue(data, SeckillOrderDetailPayload.class);
        return mapSeckillDetail(payload);
    }

    private UserOrderResponse mapSeckillSummary(SeckillOrderSummaryPayload payload) {
        UserOrderResponse response = new UserOrderResponse();
        response.setOrderId(payload.getOrderId());
        response.setOrderRef("seckill-" + payload.getOrderId());
        response.setOrderSn(payload.getOrderSn());
        response.setUserId(payload.getUserId());
        response.setUsername(firstNonBlank(payload.getUsername(), "user-" + payload.getUserId()));
        response.setStatus(payload.getStatus());
        response.setTotalAmount(defaultBigDecimal(payload.getTotalAmount()));
        response.setTotalQuantity(payload.getQuantity() == null ? 0 : payload.getQuantity());
        response.setNote("seckill order");
        response.setOrderSource(firstNonBlank(payload.getSource(), SOURCE_SECKILL));
        response.setCreatedTime(payload.getCreatedAt());

        UserOrderItemResponse item = new UserOrderItemResponse();
        item.setSkuId(payload.getSkuId());
        item.setTitle(firstNonBlank(payload.getTitle(), "秒杀商品"));
        item.setCategory("秒杀专区");
        item.setCoverUrl("");
        item.setSummary("来自 Go 秒杀 + Redis Streams + jrunmall-order 的秒杀订单");
        item.setPrice(defaultBigDecimal(payload.getTotalAmount()));
        item.setQuantity(payload.getQuantity() == null ? 0 : payload.getQuantity());
        item.setLineAmount(defaultBigDecimal(payload.getTotalAmount()));
        response.setItems(Collections.singletonList(item));
        return response;
    }

    private UserOrderResponse mapSeckillDetail(SeckillOrderDetailPayload payload) {
        UserOrderResponse response = new UserOrderResponse();
        response.setOrderId(payload.getOrderId());
        response.setOrderRef(firstNonBlank(payload.getOrderRef(), "seckill-" + payload.getOrderId()));
        response.setOrderSn(payload.getOrderSn());
        response.setUserId(payload.getUserId());
        response.setUsername(firstNonBlank(payload.getUsername(), "user-" + payload.getUserId()));
        response.setStatus(payload.getStatus());
        response.setTotalAmount(defaultBigDecimal(payload.getTotalAmount()));
        response.setTotalQuantity(payload.getTotalQuantity() == null ? 0 : payload.getTotalQuantity());
        response.setNote(payload.getNote());
        response.setOrderSource(firstNonBlank(payload.getOrderSource(), SOURCE_SECKILL));
        response.setBizToken(payload.getBizToken());
        response.setCreatedTime(payload.getCreatedTime());
        response.setPaymentTime(payload.getPaymentTime());

        List<UserOrderItemResponse> items = new ArrayList<UserOrderItemResponse>();
        if (payload.getItems() != null) {
            for (SeckillOrderItemPayload itemPayload : payload.getItems()) {
                UserOrderItemResponse item = new UserOrderItemResponse();
                item.setSkuId(itemPayload.getSkuId());
                item.setTitle(itemPayload.getTitle());
                item.setCategory(itemPayload.getCategory());
                item.setCoverUrl(itemPayload.getCoverUrl());
                item.setSummary(itemPayload.getSummary());
                item.setPrice(defaultBigDecimal(itemPayload.getPrice()));
                item.setQuantity(itemPayload.getQuantity() == null ? 0 : itemPayload.getQuantity());
                item.setLineAmount(defaultBigDecimal(itemPayload.getLineAmount()));
                items.add(item);
            }
        }
        response.setItems(items);
        return response;
    }

    private List<UserCartItemResponse> loadCartItems(Long userId) {
        HashOperations<String, Object, Object> hashOperations = stringRedisTemplate.opsForHash();
        List<Object> values = hashOperations.values(buildCartKey(userId));
        List<UserCartItemResponse> items = new ArrayList<UserCartItemResponse>();
        for (Object value : values) {
            if (value == null) {
                continue;
            }
            try {
                UserCartItemResponse item = objectMapper.readValue(String.valueOf(value), UserCartItemResponse.class);
                item.setTotalAmount(calculateLineAmount(item.getPrice(), item.getQuantity()));
                items.add(item);
            } catch (IOException ignored) {
            }
        }
        return items;
    }

    private void saveCartItems(Long userId, List<UserCartItemResponse> items) {
        String cartKey = buildCartKey(userId);
        stringRedisTemplate.delete(cartKey);
        if (items.isEmpty()) {
            return;
        }
        HashOperations<String, Object, Object> hashOperations = stringRedisTemplate.opsForHash();
        for (UserCartItemResponse item : items) {
            try {
                hashOperations.put(cartKey, String.valueOf(item.getSkuId()), objectMapper.writeValueAsString(item));
            } catch (JsonProcessingException e) {
                throw new IllegalStateException("购物车序列化失败", e);
            }
        }
    }

    private UserCartItemResponse findCartItem(List<UserCartItemResponse> items, Long skuId) {
        for (UserCartItemResponse item : items) {
            if (skuId.equals(item.getSkuId())) {
                return item;
            }
        }
        return null;
    }

    private String buildCartKey(Long userId) {
        return "jrunmall:user:cart:" + userId;
    }

    private String resolveCategoryName(Long categoryId) {
        if (categoryId == null) {
            return "未分类";
        }
        CategoryEntity category = categoryService.getById(categoryId);
        if (category == null || category.getName() == null || category.getName().trim().isEmpty()) {
            return String.valueOf(categoryId);
        }
        return category.getName().trim();
    }

    private void validateSkuId(Long skuId) {
        if (skuId == null || skuId <= 0) {
            throw new IllegalArgumentException("skuId 非法");
        }
    }

    private void validateQuantity(Integer quantity) {
        if (quantity == null || quantity <= 0 || quantity > 99) {
            throw new IllegalArgumentException("quantity 必须在 1 到 99 之间");
        }
    }

    private void validateOrderId(Long orderId) {
        if (orderId == null || orderId <= 0) {
            throw new IllegalArgumentException("orderId 非法");
        }
    }

    private Long parseOrderId(String orderRef) {
        try {
            Long orderId = Long.valueOf(orderRef);
            validateOrderId(orderId);
            return orderId;
        } catch (NumberFormatException ex) {
            throw new IllegalArgumentException("orderRef 非法");
        }
    }

    private void validateSeckillEvent(SeckillOrderEvent event) {
        if (event == null) {
            throw new IllegalArgumentException("秒杀事件不能为空");
        }
        if (event.getUserId() == null || event.getUserId() <= 0) {
            throw new IllegalArgumentException("秒杀事件 userId 非法");
        }
        validateSkuId(event.getSkuId());
        validateQuantity(event.getQuantity());
        if (event.getOrderToken() == null || event.getOrderToken().trim().isEmpty()) {
            throw new IllegalArgumentException("秒杀事件 orderToken 不能为空");
        }
    }

    private BigDecimal sumAmount(List<UserCartItemResponse> items) {
        BigDecimal total = BigDecimal.ZERO;
        for (UserCartItemResponse item : items) {
            total = total.add(calculateLineAmount(item.getPrice(), item.getQuantity()));
        }
        return total;
    }

    private Integer sumQuantity(List<UserCartItemResponse> items) {
        int total = 0;
        for (UserCartItemResponse item : items) {
            total += item.getQuantity() == null ? 0 : item.getQuantity();
        }
        return total;
    }

    private BigDecimal calculateLineAmount(BigDecimal price, Integer quantity) {
        return defaultBigDecimal(price).multiply(BigDecimal.valueOf(quantity == null ? 0 : quantity)).setScale(2, RoundingMode.HALF_UP);
    }

    private BigDecimal defaultBigDecimal(BigDecimal value) {
        return value == null ? BigDecimal.ZERO.setScale(2, RoundingMode.HALF_UP) : value.setScale(2, RoundingMode.HALF_UP);
    }

    private String firstNonBlank(String... values) {
        if (values == null) {
            return "";
        }
        for (String value : values) {
            if (value != null && !value.trim().isEmpty()) {
                return value.trim();
            }
        }
        return "";
    }

    private String generateOrderSn(Date date) {
        SimpleDateFormat format = new SimpleDateFormat("yyyyMMddHHmmssSSS", Locale.SIMPLIFIED_CHINESE);
        format.setTimeZone(TimeZone.getTimeZone("Asia/Shanghai"));
        return format.format(date) + String.format(Locale.ROOT, "%04d", new Random().nextInt(10000));
    }

    private String generateSeckillOrderSn(Date date, String orderToken) {
        String suffix = orderToken == null ? "" : orderToken.replaceAll("[^A-Za-z0-9]", "");
        if (suffix.length() > 18) {
            suffix = suffix.substring(suffix.length() - 18);
        }
        return "SK" + generateOrderSn(date) + suffix;
    }

    private String resolveSeckillUsername(Long userId) {
        return "seckill_user_" + userId;
    }

    private String joinAddress(UserAddressResponse address) {
        String merged = trim(address.getProvince()) + trim(address.getCity()) + trim(address.getRegion()) + trim(address.getDetailAddress());
        return merged.isEmpty() ? trim(address.getDetailAddress()) : merged;
    }

    private String trim(String value) {
        return value == null ? "" : value.trim();
    }

    static class SeckillOrderSummaryPayload {
        private Long orderId;
        private String orderSn;
        private Long userId;
        private String username;
        private Long skuId;
        private String title;
        private Integer quantity;
        private String status;
        private String source;
        private BigDecimal totalAmount;
        private Date createdAt;

        public Long getOrderId() { return orderId; }
        public void setOrderId(Long orderId) { this.orderId = orderId; }
        public String getOrderSn() { return orderSn; }
        public void setOrderSn(String orderSn) { this.orderSn = orderSn; }
        public Long getUserId() { return userId; }
        public void setUserId(Long userId) { this.userId = userId; }
        public String getUsername() { return username; }
        public void setUsername(String username) { this.username = username; }
        public Long getSkuId() { return skuId; }
        public void setSkuId(Long skuId) { this.skuId = skuId; }
        public String getTitle() { return title; }
        public void setTitle(String title) { this.title = title; }
        public Integer getQuantity() { return quantity; }
        public void setQuantity(Integer quantity) { this.quantity = quantity; }
        public String getStatus() { return status; }
        public void setStatus(String status) { this.status = status; }
        public String getSource() { return source; }
        public void setSource(String source) { this.source = source; }
        public BigDecimal getTotalAmount() { return totalAmount; }
        public void setTotalAmount(BigDecimal totalAmount) { this.totalAmount = totalAmount; }
        public Date getCreatedAt() { return createdAt; }
        public void setCreatedAt(Date createdAt) { this.createdAt = createdAt; }
    }

    static class SeckillOrderDetailPayload {
        private Long orderId;
        private String orderRef;
        private String orderSn;
        private Long userId;
        private String username;
        private String status;
        private BigDecimal totalAmount;
        private Integer totalQuantity;
        private String note;
        private String orderSource;
        private String bizToken;
        private Date createdTime;
        private Date paymentTime;
        private List<SeckillOrderItemPayload> items;

        public Long getOrderId() { return orderId; }
        public void setOrderId(Long orderId) { this.orderId = orderId; }
        public String getOrderRef() { return orderRef; }
        public void setOrderRef(String orderRef) { this.orderRef = orderRef; }
        public String getOrderSn() { return orderSn; }
        public void setOrderSn(String orderSn) { this.orderSn = orderSn; }
        public Long getUserId() { return userId; }
        public void setUserId(Long userId) { this.userId = userId; }
        public String getUsername() { return username; }
        public void setUsername(String username) { this.username = username; }
        public String getStatus() { return status; }
        public void setStatus(String status) { this.status = status; }
        public BigDecimal getTotalAmount() { return totalAmount; }
        public void setTotalAmount(BigDecimal totalAmount) { this.totalAmount = totalAmount; }
        public Integer getTotalQuantity() { return totalQuantity; }
        public void setTotalQuantity(Integer totalQuantity) { this.totalQuantity = totalQuantity; }
        public String getNote() { return note; }
        public void setNote(String note) { this.note = note; }
        public String getOrderSource() { return orderSource; }
        public void setOrderSource(String orderSource) { this.orderSource = orderSource; }
        public String getBizToken() { return bizToken; }
        public void setBizToken(String bizToken) { this.bizToken = bizToken; }
        public Date getCreatedTime() { return createdTime; }
        public void setCreatedTime(Date createdTime) { this.createdTime = createdTime; }
        public Date getPaymentTime() { return paymentTime; }
        public void setPaymentTime(Date paymentTime) { this.paymentTime = paymentTime; }
        public List<SeckillOrderItemPayload> getItems() { return items; }
        public void setItems(List<SeckillOrderItemPayload> items) { this.items = items; }
    }

    static class SeckillOrderItemPayload {
        private Long skuId;
        private String title;
        private String category;
        private String coverUrl;
        private String summary;
        private BigDecimal price;
        private Integer quantity;
        private BigDecimal lineAmount;

        public Long getSkuId() { return skuId; }
        public void setSkuId(Long skuId) { this.skuId = skuId; }
        public String getTitle() { return title; }
        public void setTitle(String title) { this.title = title; }
        public String getCategory() { return category; }
        public void setCategory(String category) { this.category = category; }
        public String getCoverUrl() { return coverUrl; }
        public void setCoverUrl(String coverUrl) { this.coverUrl = coverUrl; }
        public String getSummary() { return summary; }
        public void setSummary(String summary) { this.summary = summary; }
        public BigDecimal getPrice() { return price; }
        public void setPrice(BigDecimal price) { this.price = price; }
        public Integer getQuantity() { return quantity; }
        public void setQuantity(Integer quantity) { this.quantity = quantity; }
        public BigDecimal getLineAmount() { return lineAmount; }
        public void setLineAmount(BigDecimal lineAmount) { this.lineAmount = lineAmount; }
    }
}





