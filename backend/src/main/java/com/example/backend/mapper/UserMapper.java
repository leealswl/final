package com.example.backend.mapper;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import com.example.backend.domain.User;

@Mapper
public interface UserMapper {
    public int insertUser(User user);
    public User getUser(User user);
    public int deleteUser(User user);
    public int updateUser(User user);
    public int validateId(@Param("userId") String userId);
    
}
