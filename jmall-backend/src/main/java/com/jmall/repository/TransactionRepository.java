package com.jmall.repository;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.jmall.entity.Transaction;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface TransactionRepository extends BaseMapper<Transaction> {
}
