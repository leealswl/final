import React, { use, useEffect } from 'react';
import { useParams } from 'react-router-dom';

const AnalyzeSession = () => {
    const { analyzeId } = useParams();
    const isPlaceholder = analyzeId === '_new';

    useEffect(() => {
        if (isPlaceholder) return;
    }, [isPlaceholder, analyzeId]);

    return <div>AnalyzeSession - 분석 후 </div>;
};

export default AnalyzeSession;
