package com.example.backend.service;

import com.example.backend.domain.Project;

public interface ProjectService {

    public Project getProject(Long projectidx);

    public int insertProject(Project project);
    public int updateProject(Project project);
    public int deleteProject(Project project);
    
}
