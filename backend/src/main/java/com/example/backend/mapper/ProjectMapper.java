package com.example.backend.mapper;

import java.util.List;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import com.example.backend.domain.Project;

@Mapper
public interface ProjectMapper {

    public Project getProject(@Param("projectIdx") Long projectidx);
    public List<Project> getProjectList(@Param("userIdx") Long useridx);

    public int insertProject(Project project);
    public int updateProjectName(Project project);
    public int deleteProject(Project project);
    
}
