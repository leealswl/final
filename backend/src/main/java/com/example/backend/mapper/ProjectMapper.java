package com.example.backend.mapper;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import com.example.backend.domain.Project;

@Mapper
public interface ProjectMapper {

    public Project getProject(@Param("projectIdx") Long projectidx);

    public int insertProject(Project project);
    public int updateProject(Project project);
    public int deleteProject(Project project);
    
}
