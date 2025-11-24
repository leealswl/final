package com.example.backend.controller;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.example.backend.domain.User;
import com.example.backend.service.UserService;

import jakarta.servlet.http.HttpSession;

import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.PutMapping;



@RestController
@RequestMapping("/api/user/*")
public class UserController {

    @Autowired
    UserService userService;

    @PostMapping("/insert")
    public ResponseEntity<String> insertUser(@RequestBody User user) {
        int insertCount = userService.insertUser(user);
        
        return insertCount == 1 ? new ResponseEntity<String>("success", HttpStatus.OK) : new ResponseEntity<String>(HttpStatus.INTERNAL_SERVER_ERROR);
    }

    @CrossOrigin(origins = "http://localhost:5173", allowCredentials = "true")
    @PostMapping("/login")
    public ResponseEntity<?> getUser(@RequestBody User user, HttpSession session) {
        System.out.println("요청된 user: " + user);
        User loginUser = null;
        try {
            loginUser = userService.getUser(user);
            System.out.println("login user: " + loginUser);
        } catch (Exception e) {
            e.printStackTrace(); // 서버 콘솔에 예외 전체 출력
            return new ResponseEntity<>("Server error: " + e.getMessage(), HttpStatus.INTERNAL_SERVER_ERROR);
        }

        if (loginUser != null) {
            session.setAttribute("loginUser", loginUser);
            return new ResponseEntity<>(loginUser, HttpStatus.OK);
        } else {
            return new ResponseEntity<>("Invalid credentials", HttpStatus.UNAUTHORIZED);
        }
    }


    @PostMapping("/logout")
    public ResponseEntity<String> userLogout(HttpSession session) {
        session.invalidate(); // 세션 삭제

        return new ResponseEntity<String>("Log out Success", HttpStatus.OK);
    }

    @DeleteMapping("/delete")
    public ResponseEntity<String> deleteUser(@RequestBody User user) {
        int deleteCount = userService.deletetUser(user);
        
        return deleteCount == 1 ? new ResponseEntity<String>("success", HttpStatus.OK) : new ResponseEntity<String>(HttpStatus.INTERNAL_SERVER_ERROR);
    }

    @PutMapping("/update")
    public ResponseEntity<String> updateUser(@RequestBody User user) {
        int updateCount = userService.updateUser(user);
        
        return updateCount == 1 ? new ResponseEntity<String>("success", HttpStatus.OK) : new ResponseEntity<String>(HttpStatus.INTERNAL_SERVER_ERROR);
    }
    
    @GetMapping("/insert/validate/{id}")
    public ResponseEntity<String> validateId(@RequestParam String id) {
        int validateIdCount = userService.validateId(id);
        System.out.println("idcheck: " + validateIdCount);

        return validateIdCount == 0 ? new ResponseEntity<String>("success", HttpStatus.OK) : new ResponseEntity<String>(HttpStatus.INTERNAL_SERVER_ERROR);

    }
    
}
