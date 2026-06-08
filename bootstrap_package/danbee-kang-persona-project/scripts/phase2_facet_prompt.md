# Phase 2 — Facet Extraction Prompt

이 프롬프트는 강단비 교수의 논문 한 편에서 사고 흔적을 추출하는 데 사용된다.
스크립트가 abstract(또는 full text)와 함께 LLM에 전달.

---

## System

당신은 연구자의 사고 패턴을 추출하는 분석가입니다. 주어진 의학 논문에서
저자의 (1) 갭 식별 방식 (2) 문제 framing (3) 방법론 선택 논리
(4) 결과 의미 부여 (5) 자기비판 양식 (6) 다음 질문 생성 패턴을 추출합니다.

**중요한 원칙**:
- 논문에 명시되지 않은 내용을 추론·확장하지 않는다.
- 추출은 evidence pointer(어느 섹션에서 왔는지)와 함께.
- 1저자가 강단비(Danbee Kang)임을 기억하되, 공동저자 영향을 분리하려 시도하지 말 것
  (논문은 본질적으로 협업물).
- JSON만 출력. 그 외 텍스트, 주석, 코드 블록 표시 없이.

## User

다음 논문 정보에서 facet을 추출하세요.

**Metadata**:
- PMID: {pmid}
- Year: {year}
- Journal: {journal}
- Title: {title}
- DOI: {doi}

**Abstract** (또는 full text 일부):
```
{abstract_or_text}
```

다음 JSON 스키마로 출력하세요:

```json
{{
  "pmid": "{pmid}",
  "year": {year},
  "title": "...",
  "gap_statement": "이 연구가 채우려는 결핍을 1-3문장으로. 본인이 'X는 잘 모른다 / 한계가 있다'고 명시한 부분.",
  "framing_pattern": "문제를 어떻게 정의했는지. 예: '임상 의사결정에 필요한 근거 부족' / '기존 가이드라인 간 불일치' / '아시아 집단 데이터 결여' 등 카테고리화하고 본문 어구 인용.",
  "hypothesis": "검증 가설. 명시되지 않으면 명시되지 않음이라고 표기.",
  "methodology_choice": {{
    "design": "RCT / Prospective cohort / Retrospective cohort / Target trial emulation / Cross-sectional / Validation study / Systematic review / Editorial / Letter / Other",
    "data_source": "구체적 데이터원. 예: Korean NHIS / KNHANES / Samsung Medical Center prospective cohort / BIG-S registry / etc.",
    "rationale": "이 방법을 고른 이유 (논문에 명시된 경우만)."
  }},
  "key_finding": "1-2문장으로 핵심 결과.",
  "limitations": "본인이 인정한 한계 (Limitations 섹션 또는 Discussion에서). 없으면 'not stated'.",
  "future_work": "다음 연구 방향 제안 (있으면). 없으면 'not stated'.",
  "ideation_type": "다음 중 하나로 분류: 'extension' (기존 연구의 확장) | 'analogy' (다른 도메인 방법론을 이쪽에 적용) | 'combination' (두 개 이상 개념의 결합) | 'contradiction' (기존 통념에 반박) | 'methodology-import' (새로운 방법론을 본인 분야에 도입) | 'validation' (도구/스케일 검증) | 'profile' (코호트/레지스트리 소개) | 'editorial' (논평/방향 제시)",
  "evidence_pointer": "facet의 근거가 된 섹션. 'abstract' / 'introduction' / 'methods' / 'results' / 'discussion' / 'multiple'."
}}
```

JSON만 출력. 다른 텍스트 금지.
