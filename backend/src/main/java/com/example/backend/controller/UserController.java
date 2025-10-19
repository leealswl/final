package com.example.backend.controller;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.example.backend.domain.User;
import com.example.backend.service.UserService;

import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.PutMapping;



@RestController
@RequestMapping("/api/user/*")
public class UserController {

    @Autowired UserService userService;

    @PostMapping("/insert")
    public ResponseEntity<String> insertUser(@RequestBody User user) {
        int insertCount = userService.insertUser(user);
        
        return insertCount == 1 ? new ResponseEntity<String>("success", HttpStatus.OK) : new ResponseEntity<String>(HttpStatus.INTERNAL_SERVER_ERROR);
    }

    @PostMapping("/login")
    public ResponseEntity<User> getUser(@RequestBody User user) {
        System.out.println("login user: " + userService.getUser(user));
        return new ResponseEntity<>(userService.getUser(user), HttpStatus.OK);
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
