package com.example.backend.FastAPI;

import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;

@Service
public class FastAPIService {

    private final WebClient webClient = WebClient.create("http://localhost:8000");

    public String CallFastApiWithAnalsys() {

        return "test";
    }
    
}
