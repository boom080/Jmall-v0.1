package com.jmall.service;

import com.jmall.common.R;
import com.jmall.common.UserContext;
import com.jmall.entity.Product;
import com.jmall.entity.Store;
import com.jmall.entity.CartItem;
import com.jmall.repository.CartItemRepository;
import com.jmall.repository.ProductRepository;
import com.jmall.repository.StoreRepository;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.MockedStatic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.Mockito.*;

class CartServiceTest {

    private CartItemRepository cartItemRepository;
    private ProductRepository productRepository;
    private StoreRepository storeRepository;
    private CartService cartService;
    private MockedStatic<UserContext> userContext;

    @BeforeEach
    void setUp() {
        cartItemRepository = mock(CartItemRepository.class);
        productRepository = mock(ProductRepository.class);
        storeRepository = mock(StoreRepository.class);
        cartService = new CartService(cartItemRepository, productRepository, storeRepository);
        userContext = mockStatic(UserContext.class);
        userContext.when(UserContext::getUserId).thenReturn(7L);
    }

    @AfterEach
    void tearDown() {
        userContext.close();
    }

    @Test
    void addRejectsProductOwnedByCurrentUser() {
        Product product = new Product();
        product.setId(12L);
        product.setStoreId(3L);
        product.setStatus("published");
        Store store = new Store();
        store.setId(3L);
        store.setUserId(7L);
        when(productRepository.selectById(12L)).thenReturn(product);
        when(storeRepository.selectById(3L)).thenReturn(store);

        R result = cartService.add(12L, 1);

        assertEquals(10092, result.getCode());
        assertEquals("不能购买自己店铺的商品", result.getMsg());
        verify(cartItemRepository, never()).insert(any(CartItem.class));
    }

    @Test
    void addRejectsDraftProduct() {
        Product product = new Product();
        product.setId(12L);
        product.setStoreId(3L);
        product.setStatus("draft");
        when(productRepository.selectById(12L)).thenReturn(product);

        R result = cartService.add(12L, 1);

        assertEquals(10031, result.getCode());
        verify(cartItemRepository, never()).insert(any(CartItem.class));
    }
}
