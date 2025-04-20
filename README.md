# GitHub 코드 분석 도구

이 프로젝트는 GitHub 리포지토리의 코드를 자동으로 분석하고 보안 취약점을 검사하는 도구입니다. Google의 Gemini 모델과 MCP(Multi-Context Protocol)를 활용하여 코드를 분석하고 상세한 리포트를 생성합니다.

## 주요 기능

- GitHub 리포지토리에서 파일 내용 읽기
- LLM 기반 코드 분석
- 보안 취약점 검사
- 외부 통신 코드 분석
- API 출처 신뢰성 검증

## 설치 방법

1. 필요한 패키지 설치:
```bash
pip install -r requirements.txt
```

2. 환경 변수 설정:
`.env` 파일을 생성하고 다음 변수들을 설정하세요:
```
GOOGLE_API_KEY=your_google_api_key
GITHUB_PERSONAL_ACCESS_TOKEN=your_github_token
```

## 사용 방법

1. 스크립트 실행:
```bash
python test.py
```

2. 분석 결과:
- 코드 분석 요약
- 외부 통신 코드 목록
- API 출처 확인 결과
- 보안 권고 사항

## 시스템 요구사항

- Python 3.7 이상
- Google API 키
- GitHub Personal Access Token

## 라이선스

이 프로젝트는 MIT 라이선스로 배포됩니다. 