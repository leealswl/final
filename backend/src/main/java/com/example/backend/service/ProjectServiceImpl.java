package com.example.backend.service;

import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import com.example.backend.domain.Project;
import com.example.backend.mapper.ProjectMapper;

import java.util.UUID;

@Service
public class ProjectServiceImpl implements ProjectService{
    
    @Autowired
    ProjectMapper projectMapper;

    @Override
    public int deleteProject(Project project) {

        return projectMapper.deleteProject(project);
    }

    @Override
    public Project getProject(Long projectidx) {

        return projectMapper.getProject(projectidx);
    }

    @Override
    public int insertProject(Project project) {
        project.setThreadId(UUID.randomUUID().toString());

        return projectMapper.insertProject(project);
    }

    @Override
    public int updateProjectName(Project project) {

        return projectMapper.updateProjectName(project);
    }

    @Override
    public List<Project> getProjectList(Long useridx) {
        return projectMapper.getProjectList(useridx);
    }

    
}
