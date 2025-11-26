import React, { useState, useRef, useEffect } from 'react';
import { Box, Paper, Stack, Typography, TextField, Button } from '@mui/material';
import useChatbot from '../../../hooks/useChatbot';
import { useAuthStore } from '../../../store/useAuthStore';
import { useProjectStore } from '../../../store/useProjectStore';
import { useTocStore } from '../../../store/useTocStore';
import robotIcon from '../robot-icon.png.png';
import { useFileStore } from '../../../store/useFileStore';

const ChatBotMUI = () => {
    const [messages, setMessages] = useState([{ sender: 'bot', text: '안녕하세요! 기획서 작성을 도와드릴 ai도우미입니다 목차를 보고 원하는 챕터를 알려주세요' }]);
    const [inputValue, setInputValue] = useState('');
    const { mutate: sendChatMessage } = useChatbot();
    const [isLoading, setIsLoading] = useState(false);
    const setFilePath = useFileStore((s) => s.setFilePath);

    // 사용자 정보 및 프로젝트 정보 가져오기
    const user = useAuthStore((s) => s.user);
    const project = useProjectStore((s) => s.project);
    
    // 에디터 인스턴스 가져오기
    const editorInstance = useTocStore((s) => s.editorInstance);

    const scrollRef = useRef(null);
    const isComposingRef = useRef(false); // IME 조합 중인지 추적
    const pendingEnterRef = useRef(false); // 조합 종료 직후 Enter 키 대기

    const handleSend = () => {
        // 중복 호출 방지: 로딩 중이거나 입력값이 없으면 무시
        if (isLoading || !inputValue.trim()) return;

        const userText = inputValue.trim();

        setMessages((prev) => [...prev, { sender: 'user', text: userText }]);
        setInputValue('');
        setIsLoading(true);

        sendChatMessage(
            { 
                userMessage: userText,
                userIdx: user?.idx || 1,
                projectIdx: project?.projectIdx || 1
            },
            {
                onSuccess: async (data) => {
                    // 챗봇 UI용 메시지 추가
                    setMessages((prev) => [...prev, { sender: 'bot', text: data.aiResponse }]);
                    setFilePath('/uploads/admin/1/1/234.json')
                    
                    // 파일에서 JSON 읽어서 에디터에 출력
                    if (editorInstance) {
                        try {
                            // 파일 경로 설정 (캐시 방지를 위해 타임스탬프 추가)
                            const timestamp = new Date().getTime();
                            const filePath = `/uploads/admin/1/1/234.json?t=${timestamp}`;
                            
                            console.log('[ChatBotMUI] 📂 파일 읽기 시도:', filePath);
                            
                            // 파일에서 JSON 읽기 (캐시 방지 헤더 추가)
                            const response = await fetch(filePath, {
                                method: 'GET',
                                headers: {
                                    'Cache-Control': 'no-cache',
                                    'Pragma': 'no-cache'
                                }
                            });
                            
                            if (!response.ok) {
                                throw new Error(`파일 읽기 실패: ${response.status} ${response.statusText}`);
                            }
                            
                            const completedContent = await response.json();
                            console.log('[ChatBotMUI] 📄 파일 읽기 성공, paragraph 개수:', completedContent?.content?.length || 0);
                            
                            // 에디터에 반영
                            editorInstance.commands.setContent(completedContent, false);
                            console.log('[ChatBotMUI] ✅ 에디터 업데이트 완료 (파일에서 읽음)');
                        } catch (error) {
                            console.error('[ChatBotMUI] ❌ 파일 읽기 또는 에디터 업데이트 실패:', error);
                            console.error('[ChatBotMUI] 🔍 상세 오류:', error.message);
                        }
                    } else {
                        console.warn('[ChatBotMUI] ⚠️ editorInstance가 없습니다');
                    }
                    
                    setIsLoading(false);
                },
                onError: (error) => {
                    console.error('챗봇 오류:', error);
                    setMessages((prev) => [
                        ...prev,
                        { sender: 'bot', text: '⚠️ 서버 오류가 발생했습니다.' }
                    ]);
                    setIsLoading(false);
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
                                display: 'flex',
                                alignSelf: msg.sender === 'user' ? 'flex-end' : 'flex-start',
                                flexDirection: msg.sender === 'user' ? 'row-reverse' : 'row',
                                alignItems: 'flex-start',
                                gap: 1,
                                maxWidth: '80%',
                            }}
                        >
                            {msg.sender === 'bot' && (
                                <Box
                                    component="img"
                                    src={robotIcon}
                                    alt="로봇 아이콘"
                                    sx={{
                                        width: 32,
                                        height: 32,
                                        flexShrink: 0,
                                        mt: 0.5,
                                    }}
                                />
                            )}
                            <Box
                                sx={{
                                    bgcolor: msg.sender === 'user' ? 'primary.main' : 'grey.300',
                                    color: msg.sender === 'user' ? 'primary.contrastText' : 'black',
                                    p: 1.5,
                                    borderRadius: 2,
                                    wordBreak: 'break-word',
                                }}
                            >
                                <Typography variant="body2" sx={{whiteSpace: "pre-line"}}>{msg.text}</Typography>
                            </Box>
                        </Box>
                    ))}
                    {/* 🔹 AI 답변 로딩 중일 때 표시 */}
                    {isLoading && (
                        <Box
                            sx={{
                                display: 'flex',
                                alignSelf: 'flex-start',
                                alignItems: 'flex-start',
                                gap: 1,
                                maxWidth: '80%',
                            }}
                        >
                            <Box
                                component="img"
                                src={robotIcon}
                                alt="로봇 아이콘"
                                sx={{
                                    width: 32,
                                    height: 32,
                                    flexShrink: 0,
                                    mt: 0.5,
                                }}
                            />
                            <Box
                                sx={{
                                    bgcolor: 'grey.300',
                                    color: 'black',
                                    p: 1.5,
                                    borderRadius: 2,
                                    wordBreak: 'break-word',
                                }}
                            >
                                <LoadingDots />
                            </Box>
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
                            const isComposing = isComposingRef.current || (e.nativeEvent && e.nativeEvent.isComposing !== undefined ? e.nativeEvent.isComposing : false);

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
