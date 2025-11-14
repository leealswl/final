import React, { useState, useRef, useEffect } from 'react';
import { Box, Paper, Stack, Typography, TextField, Button } from '@mui/material';
import useChatbot from '../../../hooks/useChatbot';

const ChatBotMUI = () => {
    const [messages, setMessages] = useState([{ sender: 'bot', text: '안녕하세요! 무엇을 도와드릴까요?' }]);
    const [inputValue, setInputValue] = useState('');
    const { mutate: sendChatMessage } = useChatbot();
    const [isLoading, setIsLoading] = useState(false);

    // 여기 수정
    const scrollRef = useRef(null);
    const isComposingRef = useRef(false); // IME 조합 중인지 추적
    const pendingEnterRef = useRef(false); // 조합 종료 직후 Enter 키 대기

    const handleSend = () => {
        // 중복 호출 방지: 로딩 중이거나 입력값이 없으면 무시
        if (isLoading || !inputValue.trim()) return;

        const userText = inputValue.trim();

        setMessages((prev) => [...prev, { sender: 'user', text: userText }]);
        setInputValue('');
        setIsLoading(true); // 🔹 로딩 시작

        sendChatMessage(
            { userMessage: userText },
            {
                onSuccess: (data) => {
                    setMessages((prev) => [...prev, { sender: 'bot', text: data.aiResponse }]);
                    setIsLoading(false); // 🔹 로딩 종료
                },
                onError: () => {
                    setMessages((prev) => [
                        ...prev,
                        { sender: 'bot', text: '⚠️ 서버 오류가 발생했습니다.' }
                    ]);
                    setIsLoading(false); // 🔹 에러 시에도 로딩 종료
                }
        });
        
    };

    // ✅ 스크롤 항상 아래로
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages, isLoading]);

    // 🔹 로딩 애니메이션 점 찍기
    const LoadingDots = () => {
        const [dots, setDots] = useState('');
        useEffect(() => {
            const interval = setInterval(() => {
                setDots((prev) => (prev.length < 3 ? prev + '.' : ''));
            }, 500);
            return () => clearInterval(interval);
        }, []);
        return <Typography variant="body2">{`생각중이에요!${dots}`}</Typography>;
    };

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
            <Box ref={scrollRef} sx={{ flex: 1, overflowY: 'auto', mb: 2 }}>
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
                    {/* 🔹 AI 답변 로딩 중일 때 표시 */}
                    {isLoading && (
                        <Box
                            sx={{
                                alignSelf: 'flex-start',
                                bgcolor: 'grey.300',
                                color: 'black',
                                p: 1.5,
                                borderRadius: 2,
                                maxWidth: '80%',
                                wordBreak: 'break-word',
                            }}
                        >
                            <LoadingDots />
                        </Box>
                    )}
                </Stack>
            </Box>

            <Stack direction="row" spacing={1}>
                <TextField
                    variant="outlined"
                    size="small"
                    placeholder="메시지를 입력하세요..."
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onCompositionStart={() => {
                        isComposingRef.current = true; // IME 조합 시작 (macOS, Windows 공통)
                    }}
                    onCompositionUpdate={() => {
                        isComposingRef.current = true; // IME 조합 업데이트 (Windows에서 중요)
                    }}
                    onCompositionEnd={() => {
                        // 조합 종료 즉시 ref 업데이트
                        isComposingRef.current = false;
                        
                        // 조합 종료 직후 Enter 키가 눌릴 수 있으므로 짧은 시간 동안 대기
                        // onCompositionEnd와 onKeyDown의 이벤트 순서 문제 해결
                        pendingEnterRef.current = true;
                        setTimeout(() => {
                            pendingEnterRef.current = false;
                        }, 10);
                    }}
                    onKeyDown={(e) => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                            // IME 조합 중인지 확인 (Windows와 macOS 모두 지원)
                            const isComposing = isComposingRef.current || 
                                (e.nativeEvent && e.nativeEvent.isComposing !== undefined ? e.nativeEvent.isComposing : false);
                            
                            // 조합 중이 아니거나 조합 종료 직후면 전송
                            if (!isComposing || pendingEnterRef.current) {
                                e.preventDefault();
                                e.stopPropagation();
                                handleSend();
                            }
                        }
                    }}
                    fullWidth
                />
                <Button 
                    variant="contained"
                    onClick={(e) => { 
                        e.preventDefault(); 
                        e.stopPropagation();
                        handleSend();
                    }} 
                    disabled={isLoading || !inputValue.trim()}
                >
                    전송
                </Button>
            </Stack>
        </Paper>
    );
};

export default ChatBotMUI;
