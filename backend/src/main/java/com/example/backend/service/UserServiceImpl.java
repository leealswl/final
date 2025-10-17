package com.example.backend.service;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import com.example.backend.domain.User;
import com.example.backend.mapper.UserMapper;

@Service
public class UserServiceImpl implements UserService{

    @Autowired UserMapper mapper;

    @Override
    public User getUser(User user) {
        return mapper.getUser(user);
    }

    @Override
    public int insertUser(User user) {
        return mapper.insertUser(user);
    }

    @Override
    public int deletetUser(User user) {
        return mapper.deleteUser(user);
    }

    @Override
    public int updateUser(User user) {
        return mapper.updateUser(user);
    }

    @Override
    public int validateId(String userId) {
        return mapper.validateId(userId);
    }
    
}
