package com.jmall.service;

import com.jmall.common.R;
import com.jmall.common.UserContext;
import com.jmall.dto.ProductCreateRequest;
import com.jmall.dto.ProductUpdateRequest;
import com.jmall.dto.PublishBlocker;
import com.jmall.dto.PublishCheckResult;
import com.jmall.entity.Product;
import com.jmall.entity.Store;
import com.jmall.repository.ProductRepository;
import com.jmall.repository.StoreRepository;
import com.jmall.repository.UserRepository;
import io.micrometer.core.instrument.simple.SimpleMeterRegistry;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.MockedStatic;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.mockStatic;
import static org.mockito.Mockito.when;

class ProductServiceMetricsTest {

    private ProductRepository productRepository;
    private StoreRepository storeRepository;
    private ProductPublishService publishService;
    private ProductMetrics productMetrics;
    private ProductService productService;
    private SimpleMeterRegistry registry;
    private MockedStatic<UserContext> userContext;

    @BeforeEach
    void setUp() {
        productRepository = mock(ProductRepository.class);
        storeRepository = mock(StoreRepository.class);
        publishService = mock(ProductPublishService.class);
        registry = new SimpleMeterRegistry();
        productMetrics = new ProductMetrics(registry);
        productService = new ProductService(productRepository, storeRepository, mock(UserRepository.class),
                publishService, productMetrics);
        userContext = mockStatic(UserContext.class);
        userContext.when(UserContext::getUserId).thenReturn(7L);
        when(storeRepository.selectById(3L)).thenReturn(ownerStore());
        when(storeRepository.selectCount(any())).thenReturn(1L);
    }

    @AfterEach
    void tearDown() {
        userContext.close();
    }

    @Test
    void createAndDraftUpdateRecordServerAuthoritativeEvents() {
        when(storeRepository.selectOne(any())).thenReturn(ownerStore());
        ProductCreateRequest create = new ProductCreateRequest();
        create.setTitle("保温杯");
        create.setCategory("家居");
        create.setPrice(9900L);
        when(productRepository.insert(any(Product.class))).thenReturn(1);
        assertEquals(10000, productService.create(create).getCode());

        Product draft = existingProduct("draft");
        when(productRepository.selectById(12L)).thenReturn(draft);
        when(productRepository.updateById(any(Product.class))).thenReturn(1);
        assertEquals(10000, productService.update(12L, updateRequest()).getCode());

        assertEquals(1, countProduct("draft_created"));
        assertEquals(1, countProduct("draft_saved"));
    }

    @Test
    void publishAndRepeatedPublishDoNotDoubleCountPublished() {
        Product product = existingProduct("draft");
        when(productRepository.selectById(12L)).thenReturn(product);
        when(publishService.check(product)).thenReturn(new PublishCheckResult(true, List.of()));
        when(productRepository.updateById(any(Product.class))).thenReturn(1);

        assertEquals(10000, productService.publish(12L).getCode());
        assertEquals(10000, productService.publish(12L).getCode());

        assertEquals(1, countProduct("published"));
        assertEquals(0, countProduct("published_updated"));
    }

    @Test
    void publishedUpdateRecordsPublishedUpdatedAndBlockedPublishRecordsOnlyBlock() {
        Product published = existingProduct("published");
        when(productRepository.selectById(12L)).thenReturn(published);
        when(publishService.check(published)).thenReturn(new PublishCheckResult(true, List.of()));
        when(productRepository.updateById(any(Product.class))).thenReturn(1);

        assertEquals(10000, productService.update(12L, updateRequest()).getCode());
        assertEquals(1, countProduct("published_updated"));

        Product blocked = existingProduct("draft");
        when(productRepository.selectById(13L)).thenReturn(blocked);
        when(publishService.check(blocked)).thenReturn(new PublishCheckResult(false, List.of(
                new PublishBlocker("image_required", "images", "请上传图片"))));

        R result = productService.publish(13L);

        assertEquals(10034, result.getCode());
        assertEquals(1, countProduct("publish_blocked"));
        assertEquals(0, countProduct("published"));
    }

    @Test
    void publishCheckDoesNotPretendToBePublished() {
        Product product = existingProduct("draft");
        when(productRepository.selectById(12L)).thenReturn(product);
        when(publishService.check(product)).thenReturn(new PublishCheckResult(true, List.of()));

        assertEquals(10000, productService.publishCheck(12L).getCode());

        assertEquals(0, countProduct("published"));
        assertEquals(0, countProduct("publish_blocked"));
    }

    @Test
    void publishCheckRecordsGateBlockButNotMissingOrUnauthorizedProducts() {
        Product blocked = existingProduct("draft");
        when(productRepository.selectById(12L)).thenReturn(blocked);
        when(publishService.check(blocked)).thenReturn(new PublishCheckResult(false, List.of(
                new PublishBlocker("image_required", "images", "请上传图片"))));
        assertEquals(10000, productService.publishCheck(12L).getCode());
        assertEquals(1, countProduct("publish_blocked"));

        when(productRepository.selectById(99L)).thenReturn(null);
        assertEquals(10030, productService.publish(99L).getCode());

        Product unauthorized = existingProduct("draft");
        when(productRepository.selectById(100L)).thenReturn(unauthorized);
        when(storeRepository.selectCount(any())).thenReturn(0L);
        assertEquals(10010, productService.publish(100L).getCode());
        assertEquals(1, countProduct("publish_blocked"));
    }

    @Test
    void zeroAffectedRowsDoNotRecordSuccessfulEvents() {
        when(storeRepository.selectOne(any())).thenReturn(ownerStore());
        when(productRepository.insert(any(Product.class))).thenReturn(0);
        ProductCreateRequest create = new ProductCreateRequest();
        create.setTitle("未落库商品");
        assertEquals(10000, productService.create(create).getCode());

        Product product = existingProduct("draft");
        when(productRepository.selectById(12L)).thenReturn(product);
        when(productRepository.updateById(any(Product.class))).thenReturn(0);
        assertEquals(10000, productService.update(12L, updateRequest()).getCode());
        when(publishService.check(product)).thenReturn(new PublishCheckResult(true, List.of()));
        assertEquals(10000, productService.publish(12L).getCode());

        assertEquals(0, countProduct("draft_created"));
        assertEquals(0, countProduct("draft_saved"));
        assertEquals(0, countProduct("published"));
    }

    private double countProduct(String event) {
        return registry.get("jmall_product_events_total").tag("event", event).counter().count();
    }

    private Product existingProduct(String status) {
        Product product = new Product();
        product.setId(12L);
        product.setStoreId(3L);
        product.setTitle("轻量保温杯");
        product.setCategory("家居日用");
        product.setDescription("完整详情");
        product.setPrice(9900L);
        product.setStyle("taobao");
        product.setStatus(status);
        product.setViewCount(0L);
        product.setLikeCount(0L);
        product.setSaleCount(0L);
        return product;
    }

    private ProductUpdateRequest updateRequest() {
        ProductUpdateRequest request = new ProductUpdateRequest();
        request.setTitle("被修改的商品");
        request.setCategory("家居日用");
        request.setDescription("完整详情");
        request.setPrice(9900L);
        request.setStyle("taobao");
        return request;
    }

    private Store ownerStore() {
        Store store = new Store();
        store.setId(3L);
        store.setUserId(7L);
        store.setName("测试店铺");
        return store;
    }
}
