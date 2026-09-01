package com.jmall.service;

import com.jmall.common.R;
import com.jmall.common.UserContext;
import com.jmall.dto.ProductCreateRequest;
import com.jmall.dto.ProductUpdateRequest;
import com.jmall.dto.ProductResponse;
import com.jmall.dto.PublishBlocker;
import com.jmall.dto.PublishCheckResult;
import com.jmall.entity.Product;
import com.jmall.entity.Store;
import com.jmall.repository.ProductRepository;
import com.jmall.repository.StoreRepository;
import com.jmall.repository.UserRepository;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.mockito.MockedStatic;

import java.util.List;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

class ProductServiceTest {

    private ProductRepository productRepository;
    private StoreRepository storeRepository;
    private ProductPublishService publishService;
    private ProductService productService;
    private MockedStatic<UserContext> userContext;

    @BeforeEach
    void setUp() {
        productRepository = mock(ProductRepository.class);
        storeRepository = mock(StoreRepository.class);
        publishService = mock(ProductPublishService.class);
        productService = new ProductService(
                productRepository, storeRepository, mock(UserRepository.class), publishService);
        userContext = mockStatic(UserContext.class);
        userContext.when(UserContext::getUserId).thenReturn(7L);
    }

    @AfterEach
    void tearDown() {
        userContext.close();
    }

    @Test
    void createAlwaysPersistsDraft() {
        Store store = new Store();
        store.setId(3L);
        store.setUserId(7L);
        when(storeRepository.selectOne(any())).thenReturn(store);
        ProductCreateRequest request = new ProductCreateRequest();
        request.setTitle("轻量保温杯");
        request.setCategory("家居日用");
        request.setPrice(9900L);
        request.setStyle("taobao");

        R result = productService.create(request);

        assertEquals(10000, result.getCode());
        ArgumentCaptor<Product> captor = ArgumentCaptor.forClass(Product.class);
        verify(productRepository).insert(captor.capture());
        assertEquals("draft", captor.getValue().getStatus());
    }

    @Test
    void publishedUpdateFailsClosedWithoutOverwritingLiveProduct() {
        Product product = existingProduct("published");
        when(productRepository.selectById(12L)).thenReturn(product);
        when(storeRepository.selectCount(any())).thenReturn(1L);
        when(publishService.check(any())).thenReturn(new PublishCheckResult(false, List.of(
                new PublishBlocker("image_required", "images", "请上传图片"))));

        R result = productService.update(12L, updateRequest());

        assertEquals(10034, result.getCode());
        assertTrue(result.getData() instanceof PublishCheckResult);
        verify(productRepository, never()).updateById(any(Product.class));
    }

    @Test
    void publishRechecksGateAndChangesStatus() {
        Product product = existingProduct("draft");
        when(productRepository.selectById(12L)).thenReturn(product);
        when(storeRepository.selectCount(any())).thenReturn(1L);
        when(storeRepository.selectById(3L)).thenReturn(ownerStore());
        when(publishService.check(product)).thenReturn(new PublishCheckResult(true, List.of()));

        R result = productService.publish(12L);

        assertEquals(10000, result.getCode());
        assertEquals("published", product.getStatus());
        verify(productRepository).updateById(product);
    }

    @Test
    void draftDetailIsHiddenFromNonOwner() {
        Product product = existingProduct("draft");
        when(productRepository.selectById(12L)).thenReturn(product);
        Store otherStore = ownerStore();
        otherStore.setUserId(99L);
        when(storeRepository.selectById(3L)).thenReturn(otherStore);

        R result = productService.getById(12L, true);

        assertEquals(10030, result.getCode());
        verify(productRepository, never()).updateById(any(Product.class));
    }

    @Test
    void unpublishMovesOwnedProductBackToDraft() {
        Product product = existingProduct("published");
        when(productRepository.selectById(12L)).thenReturn(product);
        when(storeRepository.selectCount(any())).thenReturn(1L);
        when(storeRepository.selectById(3L)).thenReturn(ownerStore());

        R result = productService.unpublish(12L);

        assertEquals(10000, result.getCode());
        assertEquals("draft", product.getStatus());
        verify(productRepository).updateById(product);
    }

    @Test
    void skillMetadataPersistsOnCreateUpdateAndOwnerRead() {
        String meta = "{\"platform_skill_id\":\"jd_listing_v1\",\"platform_skill_version\":\"1.0.0\"}";
        String preview = "{\"target_style\":\"jd\",\"previews\":{\"jd\":{\"adapted_title\":\"保温杯\"}}}";
        when(storeRepository.selectOne(any())).thenReturn(ownerStore());
        ProductCreateRequest create = new ProductCreateRequest();
        create.setTitle("保温杯");
        create.setStyle("jd");
        create.setAiDraftMeta(meta);
        create.setAiStylePreviews(preview);
        assertEquals(10000, productService.create(create).getCode());
        ArgumentCaptor<Product> created = ArgumentCaptor.forClass(Product.class);
        verify(productRepository).insert(created.capture());
        assertEquals(meta, created.getValue().getAiDraftMeta());
        assertEquals(preview, created.getValue().getAiStylePreviews());

        Product product = existingProduct("draft");
        when(productRepository.selectById(12L)).thenReturn(product);
        when(storeRepository.selectCount(any())).thenReturn(1L);
        when(storeRepository.selectById(3L)).thenReturn(ownerStore());
        ProductUpdateRequest update = updateRequest();
        update.setAiDraftMeta(meta);
        update.setAiStylePreviews(preview);
        assertEquals(10000, productService.update(12L, update).getCode());
        assertEquals(meta, product.getAiDraftMeta());
        assertEquals(preview, product.getAiStylePreviews());
        ProductResponse recovered = (ProductResponse) productService.getById(12L, false).getData();
        assertEquals(meta, recovered.getAiDraftMeta());
        assertEquals(preview, recovered.getAiStylePreviews());
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

    private Store ownerStore() {
        Store store = new Store();
        store.setId(3L);
        store.setUserId(7L);
        store.setName("测试店铺");
        return store;
    }

    private ProductUpdateRequest updateRequest() {
        ProductUpdateRequest request = new ProductUpdateRequest();
        request.setTitle("被修改的商品");
        request.setCategory("家居日用");
        request.setDescription("");
        request.setPrice(9900L);
        request.setStyle("taobao");
        return request;
    }
}
