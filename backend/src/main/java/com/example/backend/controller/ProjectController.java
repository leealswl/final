package com.example.backend.controller;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.example.backend.domain.Project;
import com.example.backend.service.ProjectService;

import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.PutMapping;




@RestController
@RequestMapping("/api/project/*")
public class ProjectController {

    @Autowired
    ProjectService projectService;

    @GetMapping("/{projectidx}")
    public ResponseEntity<Project> getProject(@PathVariable Long projectidx) {
        return new ResponseEntity<>(projectService.getProject(projectidx), HttpStatus.OK);
    }

    @GetMapping("/list/{useridx}")
    public ResponseEntity<List<Project>> getProjectList(@PathVariable Long useridx) {
        return new ResponseEntity<>(projectService.getProjectList(useridx), HttpStatus.OK);
    }

    @PostMapping("/insert")
    public ResponseEntity<?> insertProject(@RequestBody Project project) {
        int insertCount = projectService.insertProject(project);
        System.out.println("insertCount" + insertCount);
        System.out.println("project: " + project);
        
        return insertCount == 1 ? new ResponseEntity<>(project, HttpStatus.OK) : new ResponseEntity<>(HttpStatus.INTERNAL_SERVER_ERROR);
    }

    @PutMapping("/update")
    public ResponseEntity<String> putMethodName(@RequestBody Project project) {
        int updateCount = projectService.updateProjectName(project);
        
        return updateCount == 1 ? new ResponseEntity<String>("success", HttpStatus.OK) : new ResponseEntity<String>(HttpStatus.INTERNAL_SERVER_ERROR);
    }

    @DeleteMapping("/delete")
    public ResponseEntity<String> deleteProject(@RequestBody Project project) {
        int deleteCount = projectService.deleteProject(project);
        
        return deleteCount == 1 ? new ResponseEntity<String>("success", HttpStatus.OK) : new ResponseEntity<String>(HttpStatus.INTERNAL_SERVER_ERROR);
    }
    
    
    
}
