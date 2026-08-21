package com.jmall.repository;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.jmall.entity.CartItem;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface CartItemRepository extends BaseMapper<CartItem> {
}
