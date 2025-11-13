package com.example.backend.mapper;
import org.apache.ibatis.annotations.Mapper;
import com.example.backend.domain.AiChat;
import java.util.List;

@Mapper
public interface AiChatMapper {

    void insertChat(AiChat aichat);
    List<AiChat> getAllChat();
    AiChat getChatById(Long id);
}
