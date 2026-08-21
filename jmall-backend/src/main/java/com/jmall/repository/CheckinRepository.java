package com.jmall.repository;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.jmall.entity.Checkin;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface CheckinRepository extends BaseMapper<Checkin> {
}
