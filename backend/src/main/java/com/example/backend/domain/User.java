package com.example.backend.domain;

import lombok.Data;

@Data
public class User {
    private Long idx;
    private String userId;
    private String userPw;

    public void pwEncoding(String userPw){
        this.userPw = userPw;
    }
}
