package com.jmall.repository;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.jmall.entity.Order;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface OrderRepository extends BaseMapper<Order> {
}
