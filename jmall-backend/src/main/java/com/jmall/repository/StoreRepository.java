package com.jmall.repository;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.jmall.entity.Store;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface StoreRepository extends BaseMapper<Store> {
}
