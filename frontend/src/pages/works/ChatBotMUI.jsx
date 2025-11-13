// 파일명: ChatBotMUI.jsx
import React, { useState, useRef, useEffect } from 'react';
import { Box, Paper, Stack, Typography, TextField, Button } from '@mui/material';

const ChatBotMUI = () => {
    const [messages, setMessages] = useState([{ sender: 'bot', text: '안녕하세요! 무엇을 도와드릴까요?' }]);
    const [inputValue, setInputValue] = useState('');
    const scrollRef = useRef(null);

    const handleSend = () => {
        if (!inputValue.trim()) return;

        // 사용자 메시지 추가
        setMessages((prev) => [...prev, { sender: 'user', text: inputValue }]);
        setInputValue('');

        // 예시: 봇 응답
        setTimeout(() => {
            setMessages((prev) => [...prev, { sender: 'bot', text: `봇: "${inputValue}"에 대한 답변입니다.` }]);
        }, 500);
    };

    // 스크롤 항상 아래로
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages]);

    return (
        <Paper
            elevation={3}
            sx={{
                width: '100%',
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                p: 2,
                boxSizing: 'border-box',
            }}
        >
            {/* 메시지 영역 */}
            <Box
                ref={scrollRef}
                sx={{
                    flex: 1,
                    overflowY: 'auto',
                    mb: 2,
                }}
            >
                <Stack spacing={1}>
                    {messages.map((msg, index) => (
                        <Box
                            key={index}
                            sx={{
                                alignSelf: msg.sender === 'user' ? 'flex-end' : 'flex-start',
                                bgcolor: msg.sender === 'user' ? 'primary.main' : 'grey.300',
                                color: msg.sender === 'user' ? 'primary.contrastText' : 'black',
                                p: 1.5,
                                borderRadius: 2,
                                maxWidth: '80%',
                                wordBreak: 'break-word',
                            }}
                        >
                            <Typography variant="body2">{msg.text}</Typography>
                        </Box>
                    ))}
                </Stack>
            </Box>

            {/* 입력 영역 */}
            <Stack direction="row" spacing={1}>
                <TextField
                    variant="outlined"
                    size="small"
                    placeholder="메시지를 입력하세요..."
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyDown={(e) => {
                        if (e.key === 'Enter') handleSend();
                    }}
                    fullWidth
                />
                <Button variant="contained" onClick={handleSend}>
                    전송
                </Button>
            </Stack>
        </Paper>
    );
};

export default ChatBotMUI;
