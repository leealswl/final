// import React, { useState, useEffect } from "react";
// import { 
//   Box, 
//   Button, 
//   TextField, 
//   Select, 
//   MenuItem, 
//   FormControl, 
//   InputLabel, 
//   Typography,
//   CircularProgress,
//   Chip,
//   Stack
// } from "@mui/material";

// export default function Assistant({ connector }) {
//   const [fields, setFields] = useState([]);
//   const [selectedFieldId, setSelectedFieldId] = useState(""); 
//   const [input, setInput] = useState("");
//   const [loading, setLoading] = useState(false);
//   const [connectorMethods, setConnectorMethods] = useState([]);

//   // connector의 사용 가능한 메서드 확인
//   useEffect(() => {
//     if (!connector) {
//       setConnectorMethods([]);
//       return;
//     }

//     const methods = [];
//     for (let key in connector) {
//       if (typeof connector[key] === 'function') {
//         methods.push(key);
//       }
//     }
//     setConnectorMethods(methods);
//     console.log("[Assistant] Connector 사용 가능 메서드:", methods);
//   }, [connector]);

//   // 필드 로딩
//   useEffect(() => {
//     if (!connector) {
//       setFields([]);
//       setSelectedFieldId("");
//       console.log("[Assistant] Connector가 준비되지 않아 필드 로딩을 건너뜁니다.");
//       return;
//     }

//     const timer = setTimeout(() => {
//       connector.executeMethod("GetAllContentControls", null, (fields) => {
//         const loadedFields = fields || [];
//         console.log("[Assistant] 로드된 필드:", loadedFields);
        
//         // 각 필드의 상세 정보 출력
//         loadedFields.forEach((f, idx) => {
//           console.log(`[필드 ${idx}]`, {
//             InternalId: f.InternalId,
//             Tag: f.Tag,
//             Alias: f.Alias,
//             Lock: f.Lock,
//             InternalType: f.InternalType
//           });
//         });
        
//         setFields(loadedFields);

//         if (loadedFields.length > 0) {
//           const defaultId = loadedFields[0].InternalId; 
//           setSelectedFieldId(defaultId || ""); 
//           console.log(`[Assistant] 기본 필드 InternalId 설정: ${defaultId}`);
//         } else {
//           setSelectedFieldId("");
//           console.log("[Assistant] 문서에 콘텐츠 컨트롤(필드)이 없습니다.");
//         }
//       });
//     }, 500); 

//     return () => clearTimeout(timer);
//   }, [connector]);

//   const handleChangeField = (e) => setSelectedFieldId(e.target.value);

//   // 방법 1: callCommand 사용 - 가장 단순한 방법
//   const handleAIMethod1 = () => {
//     setLoading(true);
//     const targetId = selectedFieldId;
//     const targetText = input;
    
//     console.log(`[Method1] 업데이트 시작 - ID: ${targetId}, 텍스트: "${targetText}"`);

//     const script = `
//       (function() {
//         try {
//           var oDocument = Api.GetDocument();
//           var arrControls = oDocument.GetAllContentControls();
//           var targetId = "${targetId}";
//           var targetText = "${targetText.replace(/"/g, '\\"').replace(/\n/g, '\\n')}";
          
//           for (var i = 0; i < arrControls.length; i++) {
//             var control = arrControls[i];
//             var id = String(control.GetInternalId());
            
//             if (id === targetId) {
//               // 방법 1: Range로 업데이트
//               try {
//                 var oRange = control.GetRange();
//                 oRange.Delete();
//                 oRange.AddText(targetText);
//                 return "SUCCESS:Range";
//               } catch (e1) {
//                 // 방법 2: Element로 업데이트
//                 try {
//                   control.RemoveAllElements();
//                   var oPara = Api.CreateParagraph();
//                   oPara.AddText(targetText);
//                   control.AddElement(oPara, 0);
//                   return "SUCCESS:Element";
//                 } catch (e2) {
//                   return "ERROR:" + e2.message;
//                 }
//               }
//             }
//           }
          
//           return "NOT_FOUND:ID=" + targetId + ",Count=" + arrControls.length;
//         } catch (e) {
//           return "EXCEPTION:" + e.message;
//         }
//       })();
//     `;

//     connector.callCommand(script, (result) => {
//       setLoading(false);
//       console.log("[Method1] 결과:", result);
      
//       if (typeof result === "string" && result.startsWith("SUCCESS")) {
//         alert("✅ 업데이트 성공! (" + result + ")");
//         setInput("");
//       } else if (typeof result === "string" && result.startsWith("NOT_FOUND")) {
//         alert("❌ 필드를 찾을 수 없습니다.\n" + result);
//       } else if (typeof result === "string" && result.startsWith("ERROR")) {
//         alert("❌ 오류: " + result.substring(6));
//       } else if (typeof result === "string" && result.startsWith("EXCEPTION")) {
//         alert("❌ 예외: " + result.substring(10));
//       } else {
//         alert("❌ 알 수 없는 응답: " + JSON.stringify(result));
//       }
//     });
//   };

//   // 방법 2: executeMethod 디버깅
//   const handleAIMethod2 = () => {
//     setLoading(true);
//     console.log(`[Method2] executeMethod 테스트`);
    
//     // 먼저 필드 정보 다시 가져오기
//     connector.executeMethod("GetAllContentControls", null, (allFields) => {
//       console.log("[Method2] 필드 재확인:", allFields);
      
//       const targetField = allFields.find(f => f.InternalId === selectedFieldId);
//       if (!targetField) {
//         setLoading(false);
//         alert("선택한 필드를 찾을 수 없습니다!");
//         return;
//       }
      
//       console.log("[Method2] 대상 필드:", targetField);
      
//       // Tag가 있으면 Tag로, 없으면 InternalId로 시도
//       const identifier = targetField.Tag || selectedFieldId;
//       console.log("[Method2] 사용할 식별자:", identifier);
      
//       // SetContentControlValue 재시도
//       connector.executeMethod("SetContentControlValue", [identifier, input], (result) => {
//         setLoading(false);
//         console.log("[Method2] SetContentControlValue 결과:", result);
        
//         if (result === true) {
//           alert("✅ 업데이트 성공!");
//           setInput("");
//         } else {
//           alert("❌ 업데이트 실패. Method 1을 시도해보세요.");
//         }
//       });
//     });
//   };

//   const handleAI = () => {
//     if (!connector) {
//       alert("문서가 아직 준비되지 않았어요.");
//       return;
//     }

//     const body = (input || "").trim();
//     if (!body) {
//       alert("내용을 입력해 주세요.");
//       return;
//     }
    
//     if (!selectedFieldId) {
//        alert("선택된 필드가 없습니다.");
//        return;
//     }

//     // 기본적으로 Method 1 사용
//     handleAIMethod1();
//   };

//   return (
//     <Box sx={{ p: 2, display: "grid", gap: 2, height: "100%", overflowY: 'auto' }}>
//       <Typography variant="h6" sx={{ color: 'primary.main', fontWeight: 600 }}>
//           AI 문서 도우미
//       </Typography>
      
//       {/* Connector 상태 */}
//       <Stack direction="row" spacing={1} flexWrap="wrap">
//         <Chip 
//           label={connector ? "연결됨" : "미연결"} 
//           color={connector ? "success" : "error"} 
//           size="small" 
//         />
//         {connectorMethods.length > 0 && (
//           <Chip 
//             label={`${connectorMethods.length}개 메서드`} 
//             size="small" 
//             variant="outlined"
//           />
//         )}
//         {fields.length > 0 && (
//           <Chip 
//             label={`${fields.length}개 필드`} 
//             size="small" 
//             color="primary"
//             variant="outlined"
//           />
//         )}
//       </Stack>

//       {/* 필드 선택 */}
//       <FormControl fullWidth size="small">
//         <InputLabel id="field-select-label">필드 선택</InputLabel>
//         <Select
//           labelId="field-select-label"
//           value={selectedFieldId}
//           label="필드 선택"
//           onChange={handleChangeField}
//           disabled={fields.length === 0 || loading}
//         >
//           {fields.length === 0 ? (
//               <MenuItem disabled value="">필드 없음</MenuItem>
//           ) : (
//               fields.map(f => (
//                 <MenuItem key={f.InternalId} value={f.InternalId}> 
//                   {`ID: ${f.InternalId} ${f.Tag ? `/ Tag: ${f.Tag}` : ''} ${f.Alias ? `/ ${f.Alias}` : ''}`}
//                 </MenuItem>
//               ))
//           )}
//         </Select>
//       </FormControl>

//       {/* 내용 입력 */}
//       <TextField
//         label="삽입할 텍스트"
//         value={input}
//         onChange={(e) => setInput(e.target.value)}
//         multiline
//         minRows={4}
//         fullWidth
//         disabled={loading}
//       />

//       {/* 버튼들 */}
//       <Stack direction="column" spacing={1}>
//         <Button
//           variant="contained"
//           size="large"
//           onClick={handleAI}
//           disabled={!connector || !selectedFieldId || loading}
//           startIcon={loading ? <CircularProgress size={20} /> : null}
//         >
//           {loading ? "업데이트 중..." : "문서에 넣기 (Method 1)"}
//         </Button>
        
//         <Button
//           variant="outlined"
//           size="small"
//           onClick={handleAIMethod2}
//           disabled={!connector || !selectedFieldId || loading}
//         >
//           Method 2 시도 (executeMethod)
//         </Button>
//       </Stack>
      
//       {!connector && (
//           <Typography variant="caption" color="error.main">
//               문서 에디터가 로딩되지 않았습니다.
//           </Typography>
//       )}
      
//       {/* 디버그 정보 */}
//       {connectorMethods.length > 0 && (
//         <Box sx={{ mt: 2, p: 1, bgcolor: 'grey.100', borderRadius: 1 }}>
//           <Typography variant="caption" sx={{ fontWeight: 600 }}>
//             사용 가능 메서드:
//           </Typography>
//           <Typography variant="caption" sx={{ display: 'block', fontSize: '0.7rem' }}>
//             {connectorMethods.slice(0, 10).join(', ')}
//             {connectorMethods.length > 10 ? ` (+${connectorMethods.length - 10}개)` : ''}
//           </Typography>
//         </Box>
//       )}
//     </Box>
//   );
// }


import React, { useState, useEffect } from "react";
import { 
  Box, 
  Button, 
  TextField, 
  Select, 
  MenuItem, 
  FormControl, 
  InputLabel, 
  Typography,
  CircularProgress,
  Chip,
  Stack
} from "@mui/material";

export default function Assistant2({ connector }) {
  const [fields, setFields] = useState([]);
  const [selectedFieldId, setSelectedFieldId] = useState(""); 
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [connectorMethods, setConnectorMethods] = useState([]);

  // connector의 사용 가능한 메서드 확인
  useEffect(() => {
    if (!connector) {
      setConnectorMethods([]);
      return;
    }

    const methods = [];
    for (let key in connector) {
      if (typeof connector[key] === 'function') {
        methods.push(key);
      }
    }
    setConnectorMethods(methods);
    console.log("[Assistant] Connector 사용 가능 메서드:", methods);
  }, [connector]);

  // 필드 로딩
  useEffect(() => {
    if (!connector) {
      setFields([]);
      setSelectedFieldId("");
      console.log("[Assistant] Connector가 준비되지 않아 필드 로딩을 건너뜁니다.");
      return;
    }

    const timer = setTimeout(() => {
      connector.executeMethod("GetAllContentControls", null, (fields) => {
        const loadedFields = fields || [];
        console.log("[Assistant] 로드된 필드:", loadedFields);
        
        // 각 필드의 상세 정보 출력
        loadedFields.forEach((f, idx) => {
          console.log(`[필드 ${idx}]`, {
            InternalId: f.InternalId,
            Tag: f.Tag,
            Alias: f.Alias,
            Lock: f.Lock,
            InternalType: f.InternalType
          });
        });
        
        setFields(loadedFields);

        if (loadedFields.length > 0) {
          const defaultId = loadedFields[0].InternalId; 
          setSelectedFieldId(defaultId || ""); 
          console.log(`[Assistant] 기본 필드 InternalId 설정: ${defaultId}`);
        } else {
          setSelectedFieldId("");
          console.log("[Assistant] 문서에 콘텐츠 컨트롤(필드)이 없습니다.");
        }
      });
    }, 500); 

    return () => clearTimeout(timer);
  }, [connector]);

  const handleChangeField = (e) => setSelectedFieldId(e.target.value);

  // 방법 1: callCommand 사용 - 수정된 버전
  const handleAIMethod1 = () => {
    setLoading(true);
    const targetId = selectedFieldId;
    const targetText = input;
    
    console.log(`[Method1] 업데이트 시작 - ID: ${targetId}, 텍스트: "${targetText}"`);

    const script = `
      (function() {
        try {
          var oDocument = Api.GetDocument();
          var arrControls = oDocument.GetAllContentControls();
          var targetId = "${targetId}";
          var targetText = "${targetText.replace(/"/g, '\\"').replace(/\n/g, '\\n')}";
          
          for (var i = 0; i < arrControls.length; i++) {
            var control = arrControls[i];
            var id = String(control.GetInternalId());
            
            if (id === targetId) {
              // 올바른 방법: RemoveAllElements 후 새 Paragraph 추가
              try {
                control.RemoveAllElements();
                var oPara = Api.CreateParagraph();
                oPara.AddText(targetText);
                control.AddElement(oPara, 0);
                return "SUCCESS:Updated";
              } catch (e1) {
                // 대체 방법: GetRange로 선택 후 텍스트 입력
                try {
                  var oRange = control.GetRange();
                  oRange.Select();
                  var oRun = Api.CreateRun();
                  oRun.AddText(targetText);
                  oRange.Delete();
                  control.AddElement(oRun.GetParent(), 0);
                  return "SUCCESS:Range";
                } catch (e2) {
                  return "ERROR:" + e2.message;
                }
              }
            }
          }
          
          return "NOT_FOUND:ID=" + targetId + ",Count=" + arrControls.length;
        } catch (e) {
          return "EXCEPTION:" + e.message;
        }
      })();
    `;

    connector.callCommand(script, (result) => {
      setLoading(false);
      console.log("[Method1] 결과:", result);
      
      if (typeof result === "string" && result.startsWith("SUCCESS")) {
        alert("✅ 업데이트 성공!");
        setInput("");
      } else if (typeof result === "string" && result.startsWith("NOT_FOUND")) {
        alert("❌ 필드를 찾을 수 없습니다.\n" + result);
      } else if (typeof result === "string" && result.startsWith("ERROR")) {
        alert("❌ 오류: " + result.substring(6));
      } else if (typeof result === "string" && result.startsWith("EXCEPTION")) {
        alert("❌ 예외: " + result.substring(10));
      } else {
        alert("❌ 알 수 없는 응답: " + JSON.stringify(result));
      }
    });
  };

  // 방법 2: executeMethod 디버깅
  const handleAIMethod2 = () => {
    setLoading(true);
    console.log(`[Method2] executeMethod 테스트`);
    
    // 먼저 필드 정보 다시 가져오기
    connector.executeMethod("GetAllContentControls", null, (allFields) => {
      console.log("[Method2] 필드 재확인:", allFields);
      
      const targetField = allFields.find(f => f.InternalId === selectedFieldId);
      if (!targetField) {
        setLoading(false);
        alert("선택한 필드를 찾을 수 없습니다!");
        return;
      }
      
      console.log("[Method2] 대상 필드:", targetField);
      
      // Tag가 있으면 Tag로, 없으면 InternalId로 시도
      const identifier = targetField.Tag || selectedFieldId;
      console.log("[Method2] 사용할 식별자:", identifier);
      
      // SetContentControlValue 재시도
      connector.executeMethod("SetContentControlValue", [identifier, input], (result) => {
        setLoading(false);
        console.log("[Method2] SetContentControlValue 결과:", result);
        
        if (result === true) {
          alert("✅ 업데이트 성공!");
          setInput("");
        } else {
          alert("❌ 업데이트 실패. Method 1을 시도해보세요.");
        }
      });
    });
  };

  const handleAI = () => {
    if (!connector) {
      alert("문서가 아직 준비되지 않았어요.");
      return;
    }

    const body = (input || "").trim();
    if (!body) {
      alert("내용을 입력해 주세요.");
      return;
    }
    
    if (!selectedFieldId) {
       alert("선택된 필드가 없습니다.");
       return;
    }

    // 기본적으로 Method 1 사용
    handleAIMethod1();
  };

  return (
    <Box sx={{ p: 2, display: "grid", gap: 2, height: "100%", overflowY: 'auto' }}>
      <Typography variant="h6" sx={{ color: 'primary.main', fontWeight: 600 }}>
          AI 문서 도우미
      </Typography>
      
      {/* Connector 상태 */}
      <Stack direction="row" spacing={1} flexWrap="wrap">
        <Chip 
          label={connector ? "연결됨" : "미연결"} 
          color={connector ? "success" : "error"} 
          size="small" 
        />
        {connectorMethods.length > 0 && (
          <Chip 
            label={`${connectorMethods.length}개 메서드`} 
            size="small" 
            variant="outlined"
          />
        )}
        {fields.length > 0 && (
          <Chip 
            label={`${fields.length}개 필드`} 
            size="small" 
            color="primary"
            variant="outlined"
          />
        )}
      </Stack>

      {/* 필드 선택 */}
      <FormControl fullWidth size="small">
        <InputLabel id="field-select-label">필드 선택</InputLabel>
        <Select
          labelId="field-select-label"
          value={selectedFieldId}
          label="필드 선택"
          onChange={handleChangeField}
          disabled={fields.length === 0 || loading}
        >
          {fields.length === 0 ? (
              <MenuItem disabled value="">필드 없음</MenuItem>
          ) : (
              fields.map(f => (
                <MenuItem key={f.InternalId} value={f.InternalId}> 
                  {`ID: ${f.InternalId} ${f.Tag ? `/ Tag: ${f.Tag}` : ''} ${f.Alias ? `/ ${f.Alias}` : ''}`}
                </MenuItem>
              ))
          )}
        </Select>
      </FormControl>

      {/* 내용 입력 */}
      <TextField
        label="삽입할 텍스트"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        multiline
        minRows={4}
        fullWidth
        disabled={loading}
      />

      {/* 버튼들 */}
      <Stack direction="column" spacing={1}>
        <Button
          variant="contained"
          size="large"
          onClick={handleAI}
          disabled={!connector || !selectedFieldId || loading}
          startIcon={loading ? <CircularProgress size={20} /> : null}
        >
          {loading ? "업데이트 중..." : "문서에 넣기 (Method 1)"}
        </Button>
        
        <Button
          variant="outlined"
          size="small"
          onClick={handleAIMethod2}
          disabled={!connector || !selectedFieldId || loading}
        >
          Method 2 시도 (executeMethod)
        </Button>
      </Stack>
      
      {!connector && (
          <Typography variant="caption" color="error.main">
              문서 에디터가 로딩되지 않았습니다.
          </Typography>
      )}
      
      {/* 디버그 정보 */}
      {connectorMethods.length > 0 && (
        <Box sx={{ mt: 2, p: 1, bgcolor: 'grey.100', borderRadius: 1 }}>
          <Typography variant="caption" sx={{ fontWeight: 600 }}>
            사용 가능 메서드:
          </Typography>
          <Typography variant="caption" sx={{ display: 'block', fontSize: '0.7rem' }}>
            {connectorMethods.slice(0, 10).join(', ')}
            {connectorMethods.length > 10 ? ` (+${connectorMethods.length - 10}개)` : ''}
          </Typography>
        </Box>
      )}
    </Box>
  );
}