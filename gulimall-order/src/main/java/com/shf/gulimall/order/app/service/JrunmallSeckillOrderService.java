package com.shf.gulimall.order.app.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.shf.gulimall.order.app.dto.MerchantSeckillOrderResponse;
import com.shf.gulimall.order.app.dto.SeckillOrderEvent;
import com.shf.gulimall.order.app.dto.UserSeckillOrderDetailResponse;
import com.shf.gulimall.order.app.dto.UserSeckillOrderItemResponse;
import com.shf.gulimall.order.dao.JrunmallUserOrderDao;
import com.shf.gulimall.order.dao.JrunmallUserOrderItemDao;
import com.shf.gulimall.order.entity.JrunmallUserOrderEntity;
import com.shf.gulimall.order.entity.JrunmallUserOrderItemEntity;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Date;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Random;

@Service
public class JrunmallSeckillOrderService {

    static final String STATUS_CREATED = "CREATED";
    static final String SOURCE_SECKILL = "seckill";

    private final JrunmallUserOrderDao userOrderDao;
    private final JrunmallUserOrderItemDao userOrderItemDao;
    private final JdbcTemplate jdbcTemplate;

    public JrunmallSeckillOrderService(JrunmallUserOrderDao userOrderDao,
                                       JrunmallUserOrderItemDao userOrderItemDao,
                                       JdbcTemplate jdbcTemplate) {
        this.userOrderDao = userOrderDao;
        this.userOrderItemDao = userOrderItemDao;
        this.jdbcTemplate = jdbcTemplate;
    }

    @Transactional(rollbackFor = Exception.class)
    public JrunmallUserOrderEntity createSeckillOrder(SeckillOrderEvent event) {
        validateEvent(event);

        JrunmallUserOrderEntity existing = userOrderDao.selectOne(new QueryWrapper<JrunmallUserOrderEntity>()
                .eq("biz_token", event.getOrderToken()));
        if (existing != null) {
            return existing;
        }

        SkuSnapshot sku = loadSkuSnapshot(event.getSkuId());
        Date now = event.getTimestamp() == null ? new Date() : event.getTimestamp();

        JrunmallUserOrderEntity order = new JrunmallUserOrderEntity();
        order.setOrderSn(generateSeckillOrderSn(now, event.getOrderToken()));
        order.setUserId(event.getUserId());
        order.setUsername(resolveUsername(event.getUserId()));
        order.setStatus(STATUS_CREATED);
        order.setTotalAmount(calculateLineAmount(sku.getPrice(), event.getQuantity()));
        order.setTotalQuantity(event.getQuantity());
        order.setNote("秒杀订单");
        order.setOrderSource(SOURCE_SECKILL);
        order.setBizToken(event.getOrderToken());
        order.setCreatedTime(now);
        order.setUpdatedTime(now);
        userOrderDao.insert(order);

        JrunmallUserOrderItemEntity item = new JrunmallUserOrderItemEntity();
        item.setOrderId(order.getId());
        item.setOrderSn(order.getOrderSn());
        item.setSkuId(event.getSkuId());
        item.setSpuId(sku.getSpuId());
        item.setTitle(sku.getTitle());
        item.setCategory(sku.getCategory());
        item.setCoverUrl(sku.getCoverUrl());
        item.setSummary(sku.getSummary());
        item.setPrice(sku.getPrice());
        item.setQuantity(event.getQuantity());
        item.setLineAmount(calculateLineAmount(sku.getPrice(), event.getQuantity()));
        item.setCreatedTime(now);
        userOrderItemDao.insert(item);

        return order;
    }

    public List<MerchantSeckillOrderResponse> listMerchantSeckillOrders() {
        return buildSeckillOrderResponses(null);
    }

    public List<MerchantSeckillOrderResponse> listUserSeckillOrders(Long userId) {
        return buildSeckillOrderResponses(userId);
    }

    public UserSeckillOrderDetailResponse getUserSeckillOrderDetail(Long userId, Long orderId) {
        JrunmallUserOrderEntity order = userOrderDao.selectById(orderId);
        if (order == null || !SOURCE_SECKILL.equals(order.getOrderSource())) {
            return null;
        }
        if (userId != null && !userId.equals(order.getUserId())) {
            return null;
        }

        UserSeckillOrderDetailResponse response = new UserSeckillOrderDetailResponse();
        response.setOrderId(order.getId());
        response.setOrderRef("seckill-" + order.getId());
        response.setOrderSn(order.getOrderSn());
        response.setUserId(order.getUserId());
        response.setUsername(order.getUsername());
        response.setStatus(order.getStatus());
        response.setTotalAmount(defaultBigDecimal(order.getTotalAmount()));
        response.setTotalQuantity(order.getTotalQuantity() == null ? 0 : order.getTotalQuantity());
        response.setNote(order.getNote());
        response.setOrderSource(SOURCE_SECKILL);
        response.setBizToken(order.getBizToken());
        response.setCreatedTime(order.getCreatedTime());
        response.setPaymentTime(order.getPaymentTime());

        List<JrunmallUserOrderItemEntity> items = userOrderItemDao.selectList(new QueryWrapper<JrunmallUserOrderItemEntity>()
                .eq("order_id", order.getId())
                .orderByAsc("id"));
        List<UserSeckillOrderItemResponse> detailItems = new ArrayList<UserSeckillOrderItemResponse>();
        for (JrunmallUserOrderItemEntity item : items) {
            UserSeckillOrderItemResponse detailItem = new UserSeckillOrderItemResponse();
            detailItem.setSkuId(item.getSkuId());
            detailItem.setTitle(item.getTitle());
            detailItem.setCategory(item.getCategory());
            detailItem.setCoverUrl(item.getCoverUrl());
            detailItem.setSummary(item.getSummary());
            detailItem.setPrice(defaultBigDecimal(item.getPrice()));
            detailItem.setQuantity(item.getQuantity() == null ? 0 : item.getQuantity());
            detailItem.setLineAmount(defaultBigDecimal(item.getLineAmount()));
            detailItems.add(detailItem);
        }
        response.setItems(detailItems);
        return response;
    }

    private List<MerchantSeckillOrderResponse> buildSeckillOrderResponses(Long userId) {
        QueryWrapper<JrunmallUserOrderEntity> wrapper = new QueryWrapper<JrunmallUserOrderEntity>()
                .eq("order_source", SOURCE_SECKILL)
                .orderByDesc("created_time");
        if (userId != null) {
            wrapper.eq("user_id", userId);
        }
        List<JrunmallUserOrderEntity> orders = userOrderDao.selectList(wrapper);
        if (orders == null || orders.isEmpty()) {
            return Collections.emptyList();
        }

        List<MerchantSeckillOrderResponse> responses = new ArrayList<MerchantSeckillOrderResponse>();
        for (JrunmallUserOrderEntity order : orders) {
            JrunmallUserOrderItemEntity item = firstOrderItem(order.getId());
            MerchantSeckillOrderResponse response = new MerchantSeckillOrderResponse();
            response.setOrderId(order.getId());
            response.setOrderSn(order.getOrderSn());
            response.setUserId(order.getUserId());
            response.setUsername(order.getUsername());
            response.setStatus(order.getStatus());
            response.setSource(SOURCE_SECKILL);
            response.setTotalAmount(defaultBigDecimal(order.getTotalAmount()));
            response.setCreatedAt(order.getCreatedTime());
            if (item != null) {
                response.setSkuId(item.getSkuId());
                response.setTitle(item.getTitle());
                response.setQuantity(item.getQuantity());
            } else {
                response.setTitle("Unknown SKU");
                response.setQuantity(order.getTotalQuantity() == null ? 0 : order.getTotalQuantity());
            }
            responses.add(response);
        }
        return responses;
    }

    private JrunmallUserOrderItemEntity firstOrderItem(Long orderId) {
        List<JrunmallUserOrderItemEntity> items = userOrderItemDao.selectList(new QueryWrapper<JrunmallUserOrderItemEntity>()
                .eq("order_id", orderId)
                .orderByAsc("id")
                .last("limit 1"));
        return items == null || items.isEmpty() ? null : items.get(0);
    }

    private SkuSnapshot loadSkuSnapshot(Long skuId) {
        List<Map<String, Object>> rows = jdbcTemplate.queryForList(
                "select s.sku_id, s.spu_id, s.sku_name, s.sku_title, s.sku_subtitle, s.sku_desc, " +
                        "s.sku_default_img, s.price, c.name as category_name " +
                "from jrunmall_pms.pms_sku_info s left join jrunmall_pms.pms_category c on s.catalog_id = c.cat_id where s.sku_id = ? limit 1",
                skuId);
        if (rows.isEmpty()) {
            throw new IllegalArgumentException("秒杀商品不存在");
        }

        Map<String, Object> row = rows.get(0);
        SkuSnapshot snapshot = new SkuSnapshot();
        snapshot.setSpuId(asLong(row.get("spu_id")));
        snapshot.setTitle(firstNonBlank(asString(row.get("sku_title")), asString(row.get("sku_name")), "Jrunmall 秒杀商品"));
        snapshot.setCategory(firstNonBlank(asString(row.get("category_name")), "秒杀专区"));
        snapshot.setCoverUrl(firstNonBlank(asString(row.get("sku_default_img")), ""));
        snapshot.setSummary(firstNonBlank(asString(row.get("sku_subtitle")), asString(row.get("sku_desc")), "Jrunmall 秒杀商品"));
        snapshot.setPrice(defaultBigDecimal(asBigDecimal(row.get("price"))));
        return snapshot;
    }

    private void validateEvent(SeckillOrderEvent event) {
        if (event == null) {
            throw new IllegalArgumentException("秒杀事件不能为空");
        }
        if (event.getUserId() == null || event.getUserId() <= 0) {
            throw new IllegalArgumentException("userId 非法");
        }
        if (event.getSkuId() == null || event.getSkuId() <= 0) {
            throw new IllegalArgumentException("skuId 非法");
        }
        if (event.getQuantity() == null || event.getQuantity() <= 0) {
            throw new IllegalArgumentException("quantity 非法");
        }
        if (event.getOrderToken() == null || event.getOrderToken().trim().isEmpty()) {
            throw new IllegalArgumentException("orderToken 不能为空");
        }
    }

    private String generateSeckillOrderSn(Date now, String orderToken) {
        String suffix = orderToken == null ? "" : orderToken.replaceAll("[^A-Za-z0-9]", "");
        if (suffix.length() > 10) {
            suffix = suffix.substring(suffix.length() - 10);
        }
        return "SEC" + new SimpleDateFormat("yyyyMMddHHmmss", Locale.ROOT).format(now)
                + suffix
                + String.format(Locale.ROOT, "%04d", new Random().nextInt(10000));
    }

    private String resolveUsername(Long userId) {
        if (Long.valueOf(900001L).equals(userId)) {
            return "demo-user";
        }
        return "user-" + userId;
    }

    private BigDecimal calculateLineAmount(BigDecimal price, Integer quantity) {
        return defaultBigDecimal(price).multiply(new BigDecimal(quantity == null ? 0 : quantity));
    }

    private BigDecimal defaultBigDecimal(BigDecimal value) {
        return value == null ? BigDecimal.ZERO : value;
    }

    private BigDecimal asBigDecimal(Object value) {
        if (value instanceof BigDecimal) {
            return (BigDecimal) value;
        }
        if (value == null) {
            return BigDecimal.ZERO;
        }
        return new BigDecimal(String.valueOf(value));
    }

    private Long asLong(Object value) {
        if (value == null) {
            return null;
        }
        if (value instanceof Number) {
            return ((Number) value).longValue();
        }
        return Long.valueOf(String.valueOf(value));
    }

    private String asString(Object value) {
        return value == null ? "" : String.valueOf(value);
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

    static class SkuSnapshot {
        private Long spuId;
        private String title;
        private String category;
        private String coverUrl;
        private String summary;
        private BigDecimal price;

        public Long getSpuId() {
            return spuId;
        }

        public void setSpuId(Long spuId) {
            this.spuId = spuId;
        }

        public String getTitle() {
            return title;
        }

        public void setTitle(String title) {
            this.title = title;
        }

        public String getCategory() {
            return category;
        }

        public void setCategory(String category) {
            this.category = category;
        }

        public String getCoverUrl() {
            return coverUrl;
        }

        public void setCoverUrl(String coverUrl) {
            this.coverUrl = coverUrl;
        }

        public String getSummary() {
            return summary;
        }

        public void setSummary(String summary) {
            this.summary = summary;
        }

        public BigDecimal getPrice() {
            return price;
        }

        public void setPrice(BigDecimal price) {
            this.price = price;
        }
    }
}





