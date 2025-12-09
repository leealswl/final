package com.example.backend.domain;

import java.util.Date;

import lombok.Data;

@Data
public class User {
    private Long idx;
    private String userId;
    private String userPw;
    private String userName;
    private Long roleLevel;
    private Date createdAt;
    private Date updatedAt;
    

    public void pwEncoding(String userPw){
        this.userPw = userPw;
    }
}
