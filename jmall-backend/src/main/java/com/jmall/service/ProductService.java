package com.jmall.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.jmall.common.BizCodeEnum;
import com.jmall.common.R;
import com.jmall.common.UserContext;
import com.jmall.dto.ProductCreateRequest;
import com.jmall.dto.ProductResponse;
import com.jmall.dto.ProductUpdateRequest;
import com.jmall.entity.Product;
import com.jmall.entity.Store;
import com.jmall.entity.User;
import com.jmall.repository.ProductRepository;
import com.jmall.repository.StoreRepository;
import com.jmall.repository.UserRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
public class ProductService {

    private final ProductRepository productRepository;
    private final StoreRepository storeRepository;
    private final UserRepository userRepository;

    public ProductService(ProductRepository productRepository, StoreRepository storeRepository,
                          UserRepository userRepository) {
        this.productRepository = productRepository;
        this.storeRepository = storeRepository;
        this.userRepository = userRepository;
    }

    @Transactional
    public R create(ProductCreateRequest request) {
        Long userId = UserContext.getUserId();

        // Find or auto-create user's store
        LambdaQueryWrapper<Store> storeWrapper = new LambdaQueryWrapper<>();
        storeWrapper.eq(Store::getUserId, userId);
        Store store = storeRepository.selectOne(storeWrapper);
        if (store == null) {
            store = autoCreateStore(userId);
        }

        Product product = new Product();
        product.setStoreId(store.getId());
        product.setTitle(request.getTitle());
        product.setSubtitle(request.getSubtitle());
        product.setCategory(request.getCategory());
        product.setDescription(request.getDescription());
        product.setPrice(request.getPrice());
        product.setImages(request.getImages());
        product.setStyle(request.getStyle());
        product.setAiTitle(request.getAiTitle());
        product.setAiSellingPoints(request.getAiSellingPoints());
        product.setAiDetail(request.getAiDetail());
        product.setAiStylePreviews(request.getAiStylePreviews());
        product.setMarketInsights(request.getMarketInsights());
        product.setComplianceResult(request.getComplianceResult());
        product.setStatus("published");
        product.setViewCount(0L);
        product.setLikeCount(0L);
        product.setSaleCount(0L);
        product.setCreatedAt(LocalDateTime.now());
        product.setUpdatedAt(LocalDateTime.now());
        productRepository.insert(product);

        return R.ok(product);
    }

    @Transactional
    public R update(Long id, ProductUpdateRequest request) {
        Product product = productRepository.selectById(id);
        if (product == null) {
            return R.error(BizCodeEnum.PRODUCT_NOT_FOUND);
        }

        // Verify store ownership
        LambdaQueryWrapper<Store> storeWrapper = new LambdaQueryWrapper<>();
        storeWrapper.eq(Store::getId, product.getStoreId())
                    .eq(Store::getUserId, UserContext.getUserId());
        if (storeRepository.selectCount(storeWrapper) == 0) {
            return R.error(BizCodeEnum.AUTH_ERROR);
        }

        product.setTitle(request.getTitle());
        product.setSubtitle(request.getSubtitle());
        product.setCategory(request.getCategory());
        product.setDescription(request.getDescription());
        product.setPrice(request.getPrice());
        product.setImages(request.getImages());
        product.setStyle(request.getStyle());
        product.setAiTitle(request.getAiTitle());
        product.setAiSellingPoints(request.getAiSellingPoints());
        product.setAiDetail(request.getAiDetail());
        product.setAiStylePreviews(request.getAiStylePreviews());
        product.setMarketInsights(request.getMarketInsights());
        product.setComplianceResult(request.getComplianceResult());
        product.setStatus("published");
        product.setUpdatedAt(LocalDateTime.now());
        productRepository.updateById(product);

        return R.ok(product);
    }

    @Transactional
    public R getById(Long id, boolean trackView) {
        Product product = productRepository.selectById(id);
        if (product == null) {
            return R.error(BizCodeEnum.PRODUCT_NOT_FOUND);
        }

        // A detail-page request is a real view. Persist it instead of fabricating
        // popularity with a random display multiplier.
        if (trackView) {
            product.setViewCount((product.getViewCount() == null ? 0L : product.getViewCount()) + 1);
            product.setUpdatedAt(LocalDateTime.now());
            productRepository.updateById(product);
        }

        ProductResponse response = buildProductResponse(product);
        return R.ok(response);
    }

    public R list(String category, String style, String status, String keyword, Long storeId, Integer page, Integer size) {
        int current = page != null ? page : 1;
        int pageSize = size != null ? size : 20;

        LambdaQueryWrapper<Product> wrapper = new LambdaQueryWrapper<>();
        if (StringUtils.hasText(category)) {
            wrapper.eq(Product::getCategory, category);
        }
        if (StringUtils.hasText(style)) {
            wrapper.eq(Product::getStyle, style);
        }
        if (StringUtils.hasText(status)) {
            wrapper.eq(Product::getStatus, status);
        } else {
            wrapper.eq(Product::getStatus, "published");
        }
        if (storeId != null) {
            wrapper.eq(Product::getStoreId, storeId);
        }
        if (StringUtils.hasText(keyword)) {
            wrapper.and(w -> w
                .like(Product::getTitle, keyword)
                .or()
                .like(Product::getSubtitle, keyword)
                .or()
                .like(Product::getDescription, keyword)
            );
        }
        wrapper.orderByDesc(Product::getCreatedAt);

        Page<Product> productPage = new Page<>(current, pageSize);
        productPage = productRepository.selectPage(productPage, wrapper);

        List<ProductResponse> responses = productPage.getRecords().stream()
                .map(this::buildProductResponse)
                .collect(Collectors.toList());

        return R.ok(Map.of(
                "records", responses,
                "total", productPage.getTotal(),
                "current", current,
                "size", pageSize
        ));
    }

    @Transactional
    public R delete(Long id) {
        Product product = productRepository.selectById(id);
        if (product == null) {
            return R.error(BizCodeEnum.PRODUCT_NOT_FOUND);
        }

        // Verify store ownership
        LambdaQueryWrapper<Store> storeWrapper = new LambdaQueryWrapper<>();
        storeWrapper.eq(Store::getId, product.getStoreId())
                    .eq(Store::getUserId, UserContext.getUserId());
        if (storeRepository.selectCount(storeWrapper) == 0) {
            return R.error(BizCodeEnum.AUTH_ERROR);
        }

        productRepository.deleteById(id);
        return R.ok("deleted");
    }

    @Transactional
    public void incrementSaleCount(Long productId, int quantity) {
        Product product = productRepository.selectById(productId);
        if (product != null) {
            product.setSaleCount((product.getSaleCount() == null ? 0L : product.getSaleCount()) + quantity);
            product.setUpdatedAt(LocalDateTime.now());
            productRepository.updateById(product);
        }
    }

    public R getMyProducts(Integer page, Integer size) {
        Long userId = UserContext.getUserId();
        LambdaQueryWrapper<Store> storeWrapper = new LambdaQueryWrapper<>();
        storeWrapper.eq(Store::getUserId, userId);
        Store store = storeRepository.selectOne(storeWrapper);
        if (store == null) {
            store = autoCreateStore(userId);
        }

        int current = page != null ? page : 1;
        int pageSize = size != null ? size : 20;

        LambdaQueryWrapper<Product> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(Product::getStoreId, store.getId());
        wrapper.orderByDesc(Product::getCreatedAt);

        Page<Product> productPage = new Page<>(current, pageSize);
        productPage = productRepository.selectPage(productPage, wrapper);

        List<ProductResponse> responses = productPage.getRecords().stream()
                .map(this::buildProductResponse)
                .collect(Collectors.toList());

        return R.ok(Map.of(
                "records", responses,
                "total", productPage.getTotal(),
                "current", current,
                "size", pageSize
        ));
    }

    /**
     * Auto-create a store for users who don't have one yet.
     * Ensures every user can create products without manual store setup.
     */
    private Store autoCreateStore(Long userId) {
        User user = userRepository.selectById(userId);
        String storeName = (user != null && user.getNickname() != null && !user.getNickname().isEmpty()
                ? user.getNickname() : "user") + "的店铺";

        Store store = new Store();
        store.setUserId(userId);
        store.setName(storeName);
        store.setCategory("其他");
        store.setDescription("欢迎光临！");
        store.setCreatedAt(LocalDateTime.now());
        store.setUpdatedAt(LocalDateTime.now());
        storeRepository.insert(store);

        // Link store to user
        if (user != null) {
            user.setStoreId(store.getId());
            user.setUpdatedAt(LocalDateTime.now());
            userRepository.updateById(user);
        }

        return store;
    }

    private ProductResponse buildProductResponse(Product product) {
        ProductResponse response = ProductResponse.builder()
                .id(product.getId())
                .storeId(product.getStoreId())
                .title(product.getTitle())
                .subtitle(product.getSubtitle())
                .category(product.getCategory())
                .description(product.getDescription())
                .price(product.getPrice())
                .images(product.getImages())
                .style(product.getStyle())
                .status(product.getStatus())
                .viewCount(product.getViewCount())
                .likeCount(product.getLikeCount())
                .saleCount(product.getSaleCount())
                .aiTitle(product.getAiTitle())
                .aiSellingPoints(product.getAiSellingPoints())
                .aiDetail(product.getAiDetail())
                .aiStylePreviews(product.getAiStylePreviews())
                .marketInsights(product.getMarketInsights())
                .complianceResult(product.getComplianceResult())
                .createdAt(product.getCreatedAt())
                .updatedAt(product.getUpdatedAt())
                .build();

        // Get store name
        Store store = storeRepository.selectById(product.getStoreId());
        if (store != null) {
            response.setStoreName(store.getName());
            boolean ownProduct = UserContext.getUserId() != null
                    && UserContext.getUserId().equals(store.getUserId());
            response.setPurchasable(!ownProduct && "published".equals(product.getStatus()));
            response.setUnavailableReason(ownProduct ? "不能购买自己店铺的商品" :
                    ("published".equals(product.getStatus()) ? "" : "商品已下架"));
        } else {
            response.setPurchasable(false);
            response.setUnavailableReason("店铺不存在");
        }
        return response;
    }
}
