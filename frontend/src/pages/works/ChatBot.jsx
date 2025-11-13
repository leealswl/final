import { Send, Sparkles } from 'lucide-react';
import { useState } from 'react';
import { ScrollArea } from '../main/scroll-area';

export function ChatBot() {
    const [messages, setMessages] = useState([
        {
            id: '1',
            role: 'assistant',
            content: '안녕하세요! AI 문서 작성 도우미입니다. 어떤 내용을 작성하도록 도와드릴까요?',
        },
        {
            id: '2',
            role: 'user',
            content: '사업 제안서의 서론 부분을 작성해줘',
        },
        {
            id: '3',
            role: 'assistant',
            content:
                '네, 사업 제안서의 서론을 작성해드리겠습니다. 다음 내용을 포함하면 좋을 것 같습니다:\n\n1. 제안 배경 및 목적\n2. 사업의 필요성\n3. 기대 효과\n\n구체적으로 어떤 사업에 대한 제안서인가요?',
        },
    ]);
    const [inputValue, setInputValue] = useState('');

    //태준 변경
    const handleSend =  async () => {
        if (!inputValue.trim()) return;

        const newMessage = {
            id: Date.now().toString(),
            role: 'user',
            content: inputValue,
        };

        setMessages([...messages, newMessage]);
        setInputValue('');

    try {
        const res = await fetch('http://localhost:8080/ai-chat/response', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                userMessage: newMessage.content,
                userIDx: 1,
                projectIDx: 101,
            }),
        });

        if (!res.ok) throw new Error('서버 응답 오류');

        const data = await res.json();

        const aiMessage = {
            id: Date.now().toString(),
            role: 'assistant',
            content: data.aiResponse,
        };

        setMessages((prev) => [...prev, aiMessage]);
    } catch (err) {
        console.error(err);
        const errorMessage = {
            id: Date.now().toString(),
            role: 'assistant',
            content: 'AI 응답을 불러오지 못했습니다.',
        };
        setMessages((prev) => [...prev, errorMessage]);
    }
};

    return (
        <div className="h-full bg-white flex flex-col border-r border-gray-200">
            {/* Header */}
            <div className="h-14 border-b border-gray-200 flex items-center px-4 flex-shrink-0">
                <Sparkles size={20} className="text-purple-600 mr-2" />
                <span className="text-gray-900">AI 어시스턴트</span>
            </div>

            {/* Chat Messages */}
            <ScrollArea className="flex-1 p-4">
                <div className="space-y-4 max-w-3xl mx-auto">
                    {messages.map((message) => (
                        <div key={message.id} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                            <div className={`max-w-[80%] rounded-2xl px-4 py-3 ${message.role === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-900'}`}>
                                <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                            </div>
                        </div>
                    ))}
                </div>
            </ScrollArea>

            {/* Input Area */}
            <div className="border-t border-gray-200 p-4 flex-shrink-0">
                <div className="max-w-3xl mx-auto flex gap-2">
                    <input
                        type="text"
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                        placeholder="메시지를 입력하세요..."
                        className="flex-1 px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                    <button onClick={handleSend} className="px-4 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors">
                        <Send size={20} />
                    </button>
                </div>
            </div>
        </div>
    );
}
