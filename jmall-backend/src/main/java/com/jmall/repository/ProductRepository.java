package com.jmall.repository;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.jmall.entity.Product;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface ProductRepository extends BaseMapper<Product> {
}
