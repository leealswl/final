package com.example.backend.service;

import com.example.backend.domain.User;

public interface UserService {
    public int insertUser(User user);
    public User getUser(User user);
    public int deletetUser(User user);
    public int updateUser(User user);
    public int validateId(String userId);    
}
