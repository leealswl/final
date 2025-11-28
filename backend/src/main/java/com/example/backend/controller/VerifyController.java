package com.example.backend.controller;

import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.example.backend.FastAPI.FastAPIService;
import com.example.backend.domain.Verify;

import java.util.Map;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;


@RestController
@RequestMapping("/api/verifies/*")
public class VerifyController {

    @Autowired
    FastAPIService fastAPIService;

    @PostMapping("law")
    public ResponseEntity<?> postMethodName(@RequestBody Verify payload) {
        System.out.println("VerifyController 작동");        
        Map<String, Object> result = fastAPIService.verifyLaw(payload);

        System.out.println("result: " + result);
        return new ResponseEntity<>(fastAPIService.verifyLaw(payload), HttpStatus.OK);
    }
    

}
