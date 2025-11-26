import React, { useMemo, useRef, useState, useEffect } from 'react';
import { Box, Button, Divider, IconButton, MenuItem, Select, Tabs, Tab, Tooltip, Typography } from '@mui/material';
import FormatBoldIcon from '@mui/icons-material/FormatBold';
import FormatItalicIcon from '@mui/icons-material/FormatItalic';
import FormatUnderlinedIcon from '@mui/icons-material/FormatUnderlined';
import StrikethroughSIcon from '@mui/icons-material/StrikethroughS';
import FormatListBulletedIcon from '@mui/icons-material/FormatListBulleted';
import FormatListNumberedIcon from '@mui/icons-material/FormatListNumbered';
import FormatAlignLeftIcon from '@mui/icons-material/FormatAlignLeft';
import FormatAlignCenterIcon from '@mui/icons-material/FormatAlignCenter';
import FormatAlignRightIcon from '@mui/icons-material/FormatAlignRight';
import FormatAlignJustifyIcon from '@mui/icons-material/FormatAlignJustify';
import UndoIcon from '@mui/icons-material/Undo';
import RedoIcon from '@mui/icons-material/Redo';
import TableRowsIcon from '@mui/icons-material/TableRows';
import AddPhotoAlternateIcon from '@mui/icons-material/AddPhotoAlternate';
import useDocumentSave from '../../hooks/useDocumentSave';

import CreateTableModal from './CreateTableModal';

import { asBlob } from 'html-docx-js-typescript';
import { saveAs } from 'file-saver';

const headingOptions = [
    { value: 'paragraph', label: '본문' },
    { value: 1, label: '제목 1' },
    { value: 2, label: '제목 2' },
    { value: 3, label: '제목 3' },
];

const ribbonTabs = [
    { id: 'home', label: '홈', disabled: false },
    { id: 'insert', label: '삽입', disabled: false },
    { id: 'layout', label: '레이아웃', disabled: true },
    { id: 'review', label: '검토', disabled: true },
];

const imageSizeOptions = [
    { value: 'small', label: '40%' },
    { value: 'medium', label: '60%' },
    { value: 'large', label: '80%' },
    { value: 'full', label: '100%' },
];

const RibbonSection = ({ title, children, hideTitle = false }) => (
    <Box
        sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'stretch',
            borderRight: '1px solid #E2E8F0',
            gap: 1.5,
        }}
    >
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', alignItems: 'center' }}>{children}</Box>
        {!hideTitle && title && (
            <Typography variant="caption" sx={{ textAlign: 'center', fontWeight: 600, color: '#475569' }}>
                {title}
            </Typography>
        )}
    </Box>
);

const RibbonAction = ({ title, icon: Icon, active, onClick, disabled, compact = false, hideLabel = false }) => (
    <Tooltip title={title}>
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 0.5, minWidth: compact ? 40 : 56 }}>
            <IconButton 
                sx={{ width: 'auto', padding: compact ? 0.5 : 1 }} 
                onClick={onClick} 
                color={active ? 'primary' : 'default'} 
                disabled={disabled}
                size={compact ? 'small' : 'medium'}
            >
                <Icon fontSize={compact ? 'small' : 'small'} />
            </IconButton>
            {!hideLabel && (
                <Typography variant="caption" sx={{ fontSize: compact ? 9 : 11, color: '#64748B' }}>
                    {title}
                </Typography>
            )}
        </Box>
    </Tooltip>
);

export default function Toolbar({ editor }) {
    const [activeTab, setActiveTab] = useState('home');
    const [tableModalOpen, setTableModalOpen] = useState(false);
    const imageInputRef = useRef(null);
    const { saveDocument,saving,isDirty } = useDocumentSave();
    const toolbarRef = useRef(null);
    const [isCompact, setIsCompact] = useState(false);
    const [isVeryCompact, setIsVeryCompact] = useState(false);

    // 툴바 너비 감지하여 컴팩트 모드 결정
    useEffect(() => {
        if (!toolbarRef.current) return;

        const resizeObserver = new ResizeObserver((entries) => {
            for (const entry of entries) {
                const width = entry.contentRect.width;
                setIsVeryCompact(width < 600); // 매우 작을 때
                setIsCompact(width < 800); // 작을 때
            }
        });

        resizeObserver.observe(toolbarRef.current);

        return () => {
            resizeObserver.disconnect();
        };
    }, []);

    const activeHeading = useMemo(() => {
        if (!editor) return 'paragraph';
        for (const opt of headingOptions) {
            if (typeof opt.value === 'number' && editor.isActive('heading', { level: opt.value })) {
                return opt.value;
            }
        }
        return 'paragraph';
    }, [editor]);

    const applyHeading = (value) => {
        if (!editor) return;
        if (value === 'paragraph') {
            editor.chain().focus().setParagraph().run();
        } else {
            editor.chain().focus().setHeading({ level: value }).run();
        }
    };

    const toggle = (command) => {
        if (!editor) return;
        editor.chain().focus()[command]().run();
    };

    const applyAlign = (value) => {
        if (!editor) return;
        editor.chain().focus().setTextAlign(value).run();
    };

    const handleCreateTable = ({ rows, cols, withHeaderRow }) => {
        editor?.chain().focus().insertTable({ rows, cols, withHeaderRow }).run();
    };

    const handleImageButtonClick = () => {
        imageInputRef.current?.click();
    };

    const handleImageChange = (event) => {
        const file = event.target.files?.[0];
        if (!file) return;
        if (!file.type.startsWith('image/')) {
            alert('이미지 파일만 업로드할 수 있습니다.');
            event.target.value = '';
            return;
        }
        const reader = new FileReader();
        reader.onload = () => {
            const src = reader.result;
            if (typeof src === 'string') {
                editor?.chain().focus().setImage({ src, size: 'medium' }).run();
            }
        };
        reader.onerror = () => {
            alert('이미지 로드에 실패했습니다. 다시 시도해 주세요.');
        };
        reader.readAsDataURL(file);
        event.target.value = '';
    };

    const setImageSize = (size) => {
        editor?.chain().focus().setNodeAttribute('image', 'size', size).run();
    };

    const handleTabChange = (_event, value) => {
        const tab = ribbonTabs.find((item) => item.id === value);
        if (tab?.disabled) return;
        setActiveTab(value);
    };

    // ★ 서버 저장 핸들러 (버튼에서 부를 함수)
    // const handleSaveToServer = async () => {
    //     const result = await saveDocument();
    //     if (!result.ok) {
    //     alert(result.error);
    //     } else {
    //     // 필요하면 토스트나 알림 추가
    //     // alert('저장되었습니다.');
    //     }
    // };

    // DOCX 저장 핸들러
    const handleExportDocx = async () => {
        if (!editor) return;

        // 0) 먼저 서버에 저장 (변경사항 없어도 force로 강제 저장)
        const saveResult = await saveDocument({ force: true });

        if (!saveResult.ok) {
            alert(saveResult.error || '서버 저장 중 오류가 발생했습니다.');
            return;
        }

        // 1) 에디터 내용을 HTML로 가져오기
        const htmlBody = editor.getHTML();
        console.log('htmlBody: ', htmlBody);

        const textbody = editor.getText();
        console.log('textbody: ', textbody);

        // 2) Word가 이해할 수 있는 전체 HTML 문서 형태로 감싸기
        const fullHtml = '<!DOCTYPE html>' + '<html><head><meta charset="UTF-8"></head><body>' + htmlBody + '</body></html>';

        try {
            // 3) HTML → DOCX Blob 변환
            const blob = await asBlob(fullHtml);


            // 4) 파일 저장
            saveAs(blob, '제안서초안.docx');
        } catch (err) {
            console.error('DOCX 내보내기 실패', err);
            alert('DOCX 파일 생성 중 오류가 발생했습니다.');
        }
    };

    const headingValue = typeof activeHeading === 'number' ? activeHeading : 'paragraph';
    const isImageActive = editor?.isActive('image');
    const currentImageSize = editor?.getAttributes('image')?.size || 'medium';

    return (
        <Box
            ref={toolbarRef}
            className="editor-toolbar ribbon-toolbar"
            sx={{
                display: 'flex',
                flexDirection: 'column',
                borderBottom: '1px solid #CBD5F5',
                background: 'linear-gradient(180deg, #F8FAFC 0%, #EEF2FF 100%)',
                boxShadow: '0 2px 6px rgba(15, 23, 42, 0.08)',
            }}
        >
            <Tabs
                value={activeTab}
                onChange={handleTabChange}
                variant="scrollable"
                scrollButtons="auto"
                sx={{
                    px: 2,
                    '& .MuiTab-root': {
                        minHeight: 44,
                        textTransform: 'none',
                        fontWeight: 600,
                        color: '#475569',
                    },
                    '& .Mui-selected': {
                        color: '#1D4ED8 !important',
                    },
                }}
            >
                {ribbonTabs.map((tab) => (
                    <Tab key={tab.id} value={tab.id} label={tab.label} disabled={tab.disabled} />
                ))}
            </Tabs>

            <Divider />

            {activeTab === 'home' && (
                <Box
                    sx={{
                        display: 'flex',
                        alignItems: 'stretch',
                        gap: isCompact ? 1 : 2,
                        px: isCompact ? 1 : 2,
                        py: isCompact ? 1 : 1.5,
                        '& > :last-of-type': { borderRight: 'none' },
                    }}
                >
                    {!isVeryCompact && (
                        <RibbonSection title={isCompact ? '' : '스타일'}>
                            <Box sx={{ display: 'flex', flexDirection: 'column', minWidth: isCompact ? 100 : 140, gap: 0.5 }}>
                                {!isCompact && (
                                    <Typography variant="caption" sx={{ fontSize: 11, color: '#64748B' }}>
                                        문단 스타일
                                    </Typography>
                                )}
                                <Select 
                                    size="small" 
                                    value={headingValue} 
                                    onChange={(event) => applyHeading(event.target.value)} 
                                    sx={{ 
                                        width: isCompact ? '100%' : '80%', 
                                        background: '#FFFFFF',
                                        fontSize: isCompact ? '0.75rem' : undefined,
                                    }}
                                >
                                    {headingOptions.map((option) => (
                                        <MenuItem key={option.value} value={option.value}>
                                            {option.label}
                                        </MenuItem>
                                    ))}
                                </Select>
                            </Box>
                        </RibbonSection>
                    )}

                    <RibbonSection title={isVeryCompact ? '' : (isCompact ? '' : '글꼴')}>
                        <RibbonAction 
                            title="굵게" 
                            icon={FormatBoldIcon} 
                            active={editor?.isActive('bold')} 
                            onClick={() => toggle('toggleBold')} 
                            compact={isCompact}
                            hideLabel={isVeryCompact}
                        />
                        <RibbonAction 
                            title="기울임" 
                            icon={FormatItalicIcon} 
                            active={editor?.isActive('italic')} 
                            onClick={() => toggle('toggleItalic')} 
                            compact={isCompact}
                            hideLabel={isVeryCompact}
                        />
                        {!isVeryCompact && (
                            <>
                                <RibbonAction 
                                    title="밑줄" 
                                    icon={FormatUnderlinedIcon} 
                                    active={editor?.isActive('underline')} 
                                    onClick={() => toggle('toggleUnderline')} 
                                    compact={isCompact}
                                />
                                <RibbonAction 
                                    title="취소선" 
                                    icon={StrikethroughSIcon} 
                                    active={editor?.isActive('strike')} 
                                    onClick={() => toggle('toggleStrike')} 
                                    compact={isCompact}
                                />
                            </>
                        )}
                    </RibbonSection>

                    <RibbonSection title={isVeryCompact ? '' : (isCompact ? '' : '문단')}>
                        <RibbonAction 
                            title="글머리 기호" 
                            icon={FormatListBulletedIcon} 
                            active={editor?.isActive('bulletList')} 
                            onClick={() => toggle('toggleBulletList')} 
                            compact={isCompact}
                            hideLabel={isVeryCompact}
                        />
                        <RibbonAction 
                            title="번호 매기기" 
                            icon={FormatListNumberedIcon} 
                            active={editor?.isActive('orderedList')} 
                            onClick={() => toggle('toggleOrderedList')} 
                            compact={isCompact}
                            hideLabel={isVeryCompact}
                        />
                        {!isVeryCompact && (
                            <>
                                <RibbonAction 
                                    title="왼쪽 정렬" 
                                    icon={FormatAlignLeftIcon} 
                                    active={editor?.isActive({ textAlign: 'left' })} 
                                    onClick={() => applyAlign('left')} 
                                    compact={isCompact}
                                />
                                <RibbonAction 
                                    title="가운데 정렬" 
                                    icon={FormatAlignCenterIcon} 
                                    active={editor?.isActive({ textAlign: 'center' })} 
                                    onClick={() => applyAlign('center')} 
                                    compact={isCompact}
                                />
                                <RibbonAction 
                                    title="오른쪽 정렬" 
                                    icon={FormatAlignRightIcon} 
                                    active={editor?.isActive({ textAlign: 'right' })} 
                                    onClick={() => applyAlign('right')} 
                                    compact={isCompact}
                                />
                                <RibbonAction 
                                    title="양쪽 맞춤" 
                                    icon={FormatAlignJustifyIcon} 
                                    active={editor?.isActive({ textAlign: 'justify' })} 
                                    onClick={() => applyAlign('justify')} 
                                    compact={isCompact}
                                />
                            </>
                        )}
                    </RibbonSection>

                    {!isVeryCompact && (
                        <>
                            <RibbonSection title={isCompact ? '' : '표'}>
                                <RibbonAction 
                                    title="표 삽입" 
                                    icon={TableRowsIcon} 
                                    active={false} 
                                    onClick={() => setTableModalOpen(true)} 
                                    compact={isCompact}
                                />
                            </RibbonSection>

                            <RibbonSection title={isCompact ? '' : '편집'}>
                                <RibbonAction 
                                    title="되돌리기" 
                                    icon={UndoIcon} 
                                    active={false} 
                                    onClick={() => editor?.chain().focus().undo().run()} 
                                    disabled={!editor?.can().undo()} 
                                    compact={isCompact}
                                />
                                <RibbonAction 
                                    title="다시 실행" 
                                    icon={RedoIcon} 
                                    active={false} 
                                    onClick={() => editor?.chain().focus().redo().run()} 
                                    disabled={!editor?.can().redo()} 
                                    compact={isCompact}
                                />
                            </RibbonSection>

                            <RibbonSection title={isCompact ? '' : '내보내기'}>
                                <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 0.75 }}>
                                    <Button
                                    size="small"
                                    variant="outlined"
                                    onClick={handleExportDocx}
                                    sx={{ 
                                        textTransform: 'none', 
                                        minWidth: isCompact ? 80 : 120,
                                        fontSize: isCompact ? '0.75rem' : undefined,
                                        padding: isCompact ? '4px 8px' : undefined,
                                    }}
                                    disabled={!editor || saving}
                                    >
                                    {saving ? '저장 중…' : (isCompact ? 'DOCX' : 'DOCX 저장')}
                                    </Button>
                                </Box>
                            </RibbonSection>
                        </>
                    )}
                    </Box>
            )}

            {activeTab === 'insert' && (
                <Box
                    sx={{
                        display: 'flex',
                        alignItems: 'stretch',
                        gap: 2,
                        px: 2,
                        py: 1.5,
                        '& > :last-of-type': { borderRight: 'none' },
                    }}
                >
                    <RibbonSection title="멀티미디어">
                        <RibbonAction title="이미지 삽입" icon={AddPhotoAlternateIcon} active={false} onClick={handleImageButtonClick} />
                        <input ref={imageInputRef} type="file" accept="image/*" hidden onChange={handleImageChange} />
                    </RibbonSection>
                    {isImageActive ? (
                        <RibbonSection title="이미지 서식">
                            <Box sx={{ display: 'flex', gap: 1 }}>
                                {imageSizeOptions.map((option) => (
                                    <Button
                                        key={option.value}
                                        size="small"
                                        variant={currentImageSize === option.value ? 'contained' : 'outlined'}
                                        onClick={() => setImageSize(option.value)}
                                        sx={{ textTransform: 'none', minWidth: 72 }}
                                    >
                                        {option.label}
                                    </Button>
                                ))}
                            </Box>
                        </RibbonSection>
                    ) : null}
                </Box>
            )}

            <CreateTableModal open={tableModalOpen} onClose={() => setTableModalOpen(false)} onCreate={handleCreateTable} />
        </Box>
    );
}
