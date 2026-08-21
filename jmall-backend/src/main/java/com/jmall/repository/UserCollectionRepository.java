package com.jmall.repository;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.jmall.entity.UserCollection;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface UserCollectionRepository extends BaseMapper<UserCollection> {
}
