package com.example.backend.service;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import com.example.backend.domain.Project;
import com.example.backend.mapper.ProjectMapper;

@Service
public class ProjectServiceImpl implements ProjectService{
    
    @Autowired
    ProjectMapper projectMapper;

    @Override
    public int deleteProject(Project project) {

        return 0;
    }

    @Override
    public Project getProject(Long projectidx) {

        return projectMapper.getProject(projectidx);
    }

    @Override
    public int insertProject(Project project) {

        return 0;
    }

    @Override
    public int updateProject(Project project) {

        return 0;
    }

    
}
