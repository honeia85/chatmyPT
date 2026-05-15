# data/

## seed_46papers.csv

강단비 1저자 46편의 시드 정보. 채팅 세션에서 PubMed `[1au]` 검색 후 정리.

**컬럼**: PMID, Year, Journal, Title, Design, Domain, DOI

- 40편: 채팅에서 메타데이터 분석 완료
- 6편 (2014-2018 추정): PMID만 보유, Phase 1에서 메타데이터 보강 필요

미확인 6편 PMID:
- 31913326, 30120165, 29121713, 28262081, 28233366, 26198993

## pmids_to_fetch.txt

CSV에서 PMID만 추출한 텍스트 파일.
`scripts/phase1_fetch_metadata.py`의 입력으로 사용.

각 줄에 PMID 하나씩, 총 46줄.

## 데이터 출처

- 모든 정보: PubMed (NCBI E-utilities API)
- 검색일: 2026-05-16
- 검색식: `Kang Danbee[1au]`
- 결과: total_count=46, has_more=false
