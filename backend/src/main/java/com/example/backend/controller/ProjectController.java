package com.example.backend.controller;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.example.backend.domain.Project;
import com.example.backend.service.ProjectService;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;



@RestController
@RequestMapping("/api/project/*")
public class ProjectController {

    @Autowired
    ProjectService projectService;

    @GetMapping("/{projectidx}")
    public ResponseEntity<Project> getProject(@PathVariable Long projectidx) {
        return new ResponseEntity<>(projectService.getProject(projectidx), HttpStatus.OK);
    }

    @PostMapping("insert")
    public ResponseEntity<String> insertProject(@RequestBody Project project) {
        int insertCount = projectService.insertProject(project);
        System.out.println("insertCount" + insertCount);
        
        return insertCount == 1 ? new ResponseEntity<String>("success", HttpStatus.OK) : new ResponseEntity<String>(HttpStatus.INTERNAL_SERVER_ERROR);
    }
    
    
    
}
