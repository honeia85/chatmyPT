# Qwen-1.8B 한국어 채팅 인터페이스

Qwen-1.8B 모델을 사용한 한국어 채팅 웹 인터페이스입니다.

## 특징

- Qwen-1.8B-Chat 모델 사용
- Apple Silicon(MPS) 가속 지원
- 메모리 최적화
- Gradio 웹 인터페이스
- 대화 히스토리 관리

## 시스템 요구사항

- Python 3.8 이상
- 8GB 이상의 RAM
- CUDA 지원 GPU 또는 Apple Silicon

## 설치 방법

1. 저장소 클론
```bash
git clone https://github.com/honeia85/chatmyPT.git
cd chatmyPT
```

2. 가상환경 생성 및 활성화
```bash
conda create -n qwen_chat python=3.10
conda activate qwen_chat
```

3. 필요한 패키지 설치
```bash
pip install -r requirements.txt
```

## 실행 방법

1. 가상환경 활성화
```bash
conda activate qwen_chat
```

2. 웹 인터페이스 실행
```bash
python app.py
```

3. 브라우저에서 접속
- 로컬 접속: http://localhost:7860
- 외부 접속: 실행 시 표시되는 public URL 사용

## 주의사항

- 첫 실행 시 모델 다운로드에 시간이 소요될 수 있습니다.
- Apple Silicon 사용 시 자동으로 MPS 가속을 활용합니다.
- 메모리 사용량 최적화를 위해 대화 히스토리는 최근 5개로 제한됩니다.

## 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다. 