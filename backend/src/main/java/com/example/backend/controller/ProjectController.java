package com.example.backend.controller;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.example.backend.domain.Project;
import com.example.backend.service.ProjectService;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;


@RestController
@RequestMapping("/api/project/*")
public class ProjectController {

    @Autowired
    ProjectService projectService;

    @GetMapping("/{projectidx}")
    public ResponseEntity<Project> getProject(@RequestParam Long projectidx) {
        return new ResponseEntity<>(projectService.getProject(projectidx), HttpStatus.OK);
    }
    
    
}
