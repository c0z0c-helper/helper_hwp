# RAG 기반 PEP 문서 처리 시스템 설계서

## 프로젝트 개요

hwp 변환 프로그램을 helper_hwp.py로 파이선 코딩
helper_hwp.py 파이선 코드로의 변환이 잘되었는지 검토 해야한다.
파일형식 5.0을 기준으로 만들자
test_helper_hwp.py는 test.hwp를 helper_hwp.py 이용하여 테스트한 소스이다.
테스트 소스를 기반으로 정상적인 동작을 검토 하자.
오류 발생시 docs 문서를 참고 하여 디버깅 하자

## 개발 원칙
- **MVP 최적화**: 재현성(reproducibility) 우선
- **코드 제안 단위**: 함수/메서드/클래스 단위
- **로깅**: `print` 최소화, 로깅 우선
- **코드 길이 규칙**
  - MVP
- **스타일 가이드**
  - PEP 8 + Black + isort
  - PEP 484 (타입힌트), PEP 257 (Docstring)
