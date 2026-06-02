package com.shf.gulimall.product.app.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.shf.gulimall.product.app.dto.CurrentUserProfile;
import com.shf.gulimall.product.app.dto.SeckillDealResponse;
import com.shf.gulimall.product.app.dto.SeckillOrderEvent;
import com.shf.gulimall.product.app.dto.SeckillSubmitRequest;
import com.shf.gulimall.product.app.dto.SeckillSubmitPublicResponse;
import com.shf.gulimall.product.app.dto.SeckillSubmitResponse;
import com.shf.gulimall.product.app.dto.UserOrderResponse;
import com.shf.gulimall.product.config.JrunmallPlatformProperties;
import com.shf.gulimall.product.entity.CategoryEntity;
import com.shf.gulimall.product.entity.SkuInfoEntity;
import com.shf.gulimall.product.service.CategoryService;
import com.shf.gulimall.product.service.SkuInfoService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.HttpStatusCodeException;
import org.springframework.web.client.RestTemplate;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.UUID;

@Service
public class UserSeckillApplicationService {

    private static final String DEFAULT_SECKILL_COVER_URL = "/placeholders/products/seckill-product.svg";

    private final JrunmallPlatformProperties platformProperties;
    private final CurrentUserResolver currentUserResolver;
    private final UserCommerceApplicationService userCommerceApplicationService;
    private final SkuInfoService skuInfoService;
    private final CategoryService categoryService;
    private final RestTemplate restTemplate;
    private final ObjectMapper objectMapper = new ObjectMapper();

    @Autowired
    public UserSeckillApplicationService(JrunmallPlatformProperties platformProperties,
                                         CurrentUserResolver currentUserResolver,
                                         UserCommerceApplicationService userCommerceApplicationService,
                                         SkuInfoService skuInfoService,
                                         CategoryService categoryService) {
        this(platformProperties, currentUserResolver, userCommerceApplicationService, skuInfoService, categoryService, new RestTemplate());
    }

    UserSeckillApplicationService(JrunmallPlatformProperties platformProperties,
                                  CurrentUserResolver currentUserResolver,
                                  UserCommerceApplicationService userCommerceApplicationService,
                                  SkuInfoService skuInfoService,
                                  CategoryService categoryService,
                                  RestTemplate restTemplate) {
        this.platformProperties = platformProperties;
        this.currentUserResolver = currentUserResolver;
        this.userCommerceApplicationService = userCommerceApplicationService;
        this.skuInfoService = skuInfoService;
        this.categoryService = categoryService;
        this.restTemplate = restTemplate;
    }

    public SeckillDealResponse currentDeal() {
        SkuInfoEntity sku = loadConfiguredSku();
        SeckillDealResponse response = new SeckillDealResponse();
        response.setTitle(firstNonBlank(sku.getSkuTitle(), sku.getSkuName(), "Jrunmall 秒杀商品"));
        response.setCategory(resolveCategoryName(sku.getCatalogId()));
        response.setCoverUrl(firstNonBlank(sku.getSkuDefaultImg(), DEFAULT_SECKILL_COVER_URL));
        response.setSummary(firstNonBlank(sku.getSkuSubtitle(), sku.getSkuDesc(), "限时秒杀商品"));
        response.setPrice(sku.getPrice());
        response.setLimitPerOrder(resolveLimitPerOrder());
        return response;
    }

    public SeckillSubmitPublicResponse submit(SeckillSubmitRequest request) {
        CurrentUserProfile user = currentUserResolver.requireCurrentUser();
        validate(request);

        Map<String, Object> payload = new LinkedHashMap<String, Object>();
        payload.put("activityId", resolveActivityId());
        payload.put("skuId", resolveSkuId());
        payload.put("userId", String.valueOf(user.getUserId()));
        payload.put("requestId", resolveRequestId(request.getRequestId()));
        payload.put("quantity", request.getQuantity() == null ? 1 : request.getQuantity());

        String url = seckillServiceBaseUrl() + "/api/seckill/submit";
        SeckillSubmitResponse body = postForSeckill(url, payload);
        if (shouldWarmupAndRetry(body)) {
            warmupCurrentActivity();
            body = postForSeckill(url, payload);
        }
        if (body == null) {
            throw new IllegalStateException("Go 秒杀服务返回为空");
        }
        return toPublicResponse(body);
    }

    private SeckillSubmitResponse postForSeckill(String url, Map<String, Object> payload) {
        try {
            ResponseEntity<SeckillSubmitResponse> response = restTemplate.postForEntity(url, payload, SeckillSubmitResponse.class);
            return response.getBody();
        } catch (HttpStatusCodeException ex) {
            try {
                return objectMapper.readValue(ex.getResponseBodyAsString(), SeckillSubmitResponse.class);
            } catch (Exception ignored) {
                throw ex;
            }
        }
    }

    private void validate(SeckillSubmitRequest request) {
        if (request == null) {
            throw new IllegalArgumentException("秒杀请求不能为空");
        }
        int limit = resolveLimitPerOrder();
        if (request.getQuantity() != null && (request.getQuantity() <= 0 || request.getQuantity() > limit)) {
            throw new IllegalArgumentException("quantity 必须在 1 到 " + limit + " 之间");
        }
        resolveActivityId();
        resolveSkuId();
    }

    private boolean shouldWarmupAndRetry(SeckillSubmitResponse body) {
        if (body == null) {
            return false;
        }
        if ("ACTIVITY_NOT_FOUND".equals(body.getCode())) {
            return true;
        }
        return "SOLD_OUT".equals(body.getCode()) && shouldAutoWarmupOnSoldOut();
    }

    private void warmupCurrentActivity() {
        Map<String, Object> payload = new LinkedHashMap<String, Object>();
        payload.put("activityId", resolveActivityId());
        payload.put("skuId", resolveSkuId());
        payload.put("stock", resolveWarmupStock());

        String url = seckillServiceBaseUrl() + "/api/seckill/warmup";
        restTemplate.postForEntity(url, payload, Map.class);
    }

    private String seckillServiceBaseUrl() {
        return trimRight(platformProperties.getUserSide().getSeckillServiceUrl(), "/");
    }

    private String resolveRequestId(String requestId) {
        if (requestId != null && !requestId.trim().isEmpty()) {
            return requestId.trim();
        }
        return UUID.randomUUID().toString();
    }

    private String trimRight(String value, String suffix) {
        if (value == null || value.trim().isEmpty()) {
            return "http://127.0.0.1:19090";
        }
        String result = value.trim();
        while (result.endsWith(suffix)) {
            result = result.substring(0, result.length() - suffix.length());
        }
        return result;
    }

    private SeckillSubmitPublicResponse toPublicResponse(SeckillSubmitResponse internal) {
        SeckillSubmitPublicResponse response = new SeckillSubmitPublicResponse();
        response.setAccepted(Boolean.TRUE.equals(internal.getAccepted()));
        response.setCode(internal.getCode());
        response.setMessage(toUserFacingMessage(internal));
        response.setQuantity(internal.getQuantity());

        if ((Boolean.TRUE.equals(internal.getAccepted()) || "DUPLICATE_REQUEST".equals(internal.getCode()))
                && internal.getOrderToken() != null && !internal.getOrderToken().trim().isEmpty()) {
            UserOrderResponse order = userCommerceApplicationService.createSeckillOrder(toOrderEvent(internal));
            response.setOrderId(order.getOrderId());
            response.setOrderRef(order.getOrderRef());
            response.setOrderSn(order.getOrderSn());
            response.setAccepted(true);
            if ("DUPLICATE_REQUEST".equals(internal.getCode())) {
                response.setMessage("你已经抢到该商品，请继续确认地址并完成支付。");
            }
        }
        return response;
    }

    private SeckillOrderEvent toOrderEvent(SeckillSubmitResponse internal) {
        SeckillOrderEvent event = new SeckillOrderEvent();
        event.setUserId(Long.valueOf(internal.getUserId()));
        event.setSkuId(internal.getSkuId());
        event.setQuantity(internal.getQuantity());
        event.setOrderToken(internal.getOrderToken());
        event.setSeckillSessionId(internal.getSeckillSessionId());
        return event;
    }

    private String toUserFacingMessage(SeckillSubmitResponse internal) {
        String code = internal.getCode();
        if ("ACCEPTED".equals(code)) {
            return "抢购成功，请继续确认收货地址并完成支付。";
        }
        if ("DUPLICATE_REQUEST".equals(code)) {
            return "你已经提交过本场秒杀，请继续查看订单。";
        }
        if ("SOLD_OUT".equals(code)) {
            return "本场秒杀商品已售罄。";
        }
        if ("NOT_STARTED".equals(code)) {
            return "本场秒杀尚未开始。";
        }
        if ("ENDED".equals(code)) {
            return "本场秒杀已结束。";
        }
        if ("ACTIVITY_NOT_FOUND".equals(code)) {
            return "秒杀活动尚未就绪，请稍后再试。";
        }
        return firstNonBlank(internal.getMessage(), "秒杀请求未受理");
    }

    private SkuInfoEntity loadConfiguredSku() {
        Long skuId = resolveSkuId();
        SkuInfoEntity sku = skuInfoService.getById(skuId);
        if (sku == null) {
            throw new IllegalArgumentException("当前秒杀商品未配置或不存在");
        }
        return sku;
    }

    private String resolveActivityId() {
        String activityId = platformProperties.getUserSide().getSeckillActivityId();
        if (activityId == null || activityId.trim().isEmpty()) {
            throw new IllegalArgumentException("秒杀活动未配置");
        }
        return activityId.trim();
    }

    private Long resolveSkuId() {
        Long skuId = platformProperties.getUserSide().getSeckillSkuId();
        if (skuId == null || skuId <= 0) {
            throw new IllegalArgumentException("秒杀商品未配置");
        }
        return skuId;
    }

    private int resolveLimitPerOrder() {
        Integer limit = platformProperties.getUserSide().getSeckillLimitPerOrder();
        return limit == null || limit <= 0 ? 1 : Math.min(limit, 5);
    }

    private int resolveWarmupStock() {
        Integer stock = platformProperties.getUserSide().getSeckillWarmupStock();
        return stock == null || stock <= 0 ? 50 : stock;
    }

    private boolean shouldAutoWarmupOnSoldOut() {
        return !Boolean.FALSE.equals(platformProperties.getUserSide().getSeckillAutoWarmupOnSoldOut());
    }

    private String resolveCategoryName(Long catalogId) {
        if (catalogId == null) {
            return "秒杀专区";
        }
        CategoryEntity category = categoryService.getById(catalogId);
        return category == null ? "秒杀专区" : firstNonBlank(category.getName(), "秒杀专区");
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
}





