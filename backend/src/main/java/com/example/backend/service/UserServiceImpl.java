package com.example.backend.service;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import com.example.backend.domain.User;
import com.example.backend.mapper.UserMapper;

@Service
public class UserServiceImpl implements UserService{

    @Autowired UserMapper userMapper;

    @Override
    public User getUser(User user) {
        return userMapper.getUser(user);
    }

    @Override
    public int insertUser(User user) {
        return userMapper.insertUser(user);
    }

    @Override
    public int deletetUser(User user) {
        return userMapper.deleteUser(user);
    }

    @Override
    public int updateUser(User user) {
        return userMapper.updateUser(user);
    }

    @Override
    public int validateId(String userId) {
        return userMapper.validateId(userId);
    }
    
}
