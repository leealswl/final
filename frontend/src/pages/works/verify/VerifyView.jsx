import { useEffect, useState } from 'react';
import { draftApi } from '../../../utils/draftApi';
import { tiptapDocToPlainText } from '../../../utils/tiptapText';
import { verifyLawSection } from '../../../utils/fastapi';

const FOCUSES = [
  {
    key: 'purpose',
    label: '사업 목적/필요성/국가 R&D 기본 원칙',
    focus: '사업 목적/필요성/국가 R&D 기본 원칙 관점에서 이 초안을 검토하라.',
  },
  {
    key: 'budget',
    label: '연구개발비·예산(직접비/간접비/자부담 등)',
    focus: '연구개발비 및 예산(직접비/간접비/자부담 등) 관점에서 이 초안을 검토하라.',
  },
  {
    key: 'structure',
    label: '수행체계·책임·참여제한',
    focus: '수행체계, 책임, 참여제한(국가연구개발혁신법 및 시행령) 관점에서 이 초안을 검토하라.',
  },
  {
    key: 'outcome',
    label: '성과지표·평가·성과관리',
    focus: '성과지표, 평가, 성과관리(성과평가 관련 법 및 시행령) 관점에서 이 초안을 검토하라.',
  },
];

function VerifyLawTestView() {
  const [text, setText] = useState('');
  const [results, setResults] = useState({}); // 관점별 결과
  const [loading, setLoading] = useState(false);

  // ✅ 초안 JSON → plain text 변환
  useEffect(() => {
    (async () => {
      try {
        const docJson = await draftApi();        // 234.json 요청
        const plain = tiptapDocToPlainText(docJson); // Tiptap JSON → 텍스트
        console.log('초안 텍스트:', plain);
        setText(plain);
      } catch (e) {
        console.error('초안 JSON 불러오기 실패', e);
      }
    })();
  }, []);

  // ✅ 2) 네 개 관점 한 번에 검증
   const handleVerifyAll = async () => {
    if (!text) {
      alert('초안 텍스트가 없습니다.');
      return;
    }

    try {
      setLoading(true);
      setResults({});

      // /verify/law를 관점별로 네 번 호출 (verifyLawSection 함수 사용)
      const promises = FOCUSES.map((f) =>
        verifyLawSection({ text, focus: f.focus }).then((apiRes) => ({
          key: f.key,
          label: f.label,
          data: apiRes.data,
        }))
      );

      const resolved = await Promise.all(promises);

      const next = {};
      resolved.forEach((r) => {
        next[r.key] = {
          label: r.label,
          ...r.data,
        };
      });

      setResults(next);
    } catch (e) {
      console.error('법령 검증 실패', e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: 24 }}>
      <h2>법령 검증 테스트</h2>

      <button onClick={handleVerifyAll} disabled={loading || !text}>
        {loading ? '검증 중...' : '검증 고고'}
      </button>

      <h3 style={{ marginTop: 24 }}>초안 텍스트</h3>
      <pre style={{ whiteSpace: 'pre-wrap', background: '#f5f5f5', padding: 12 }}>
        {text || '(초안 로딩 중 또는 없음)'}
      </pre>

      <h3 style={{ marginTop: 24 }}>관점별 검증 결과</h3>

      {FOCUSES.map((f) => {
        const r = results[f.key];
        return (
          <div
            key={f.key}
            style={{
              marginTop: 16,
              padding: 12,
              border: '1px solid #ddd',
              borderRadius: 8,
            }}
          >
            <h4>{f.label}</h4>
            {r ? (
              <pre style={{ whiteSpace: 'pre-wrap' }}>
                {JSON.stringify(r, null, 2)}
              </pre>
            ) : (
              <p style={{ color: '#888' }}>아직 결과 없음</p>
            )}
          </div>
        );
      })}
    </div>
  );
}

export default VerifyLawTestView;
