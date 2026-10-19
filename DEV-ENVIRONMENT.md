# 개발 환경

확인일: 2026-10-19
각 `--version` 결과는 실행한 출력을 그대로 적었다.

## 운영체제와 셸
- 운영체제: Microsoft Windows 11 Pro 10.0.22631
- 셸: PowerShell 7.6.7 (Git Bash도 사용 가능)

## 도구별 버전

| 도구 | 실행한 명령 | 결과 |
|---|---|---|
| git | `git --version` | `git version 2.56.0.windows.2` |
| node | `node --version` | 설치되어 있지 않음. 명령을 찾을 수 없다는 오류가 나옴 |
| npm | `npm --version` | 설치되어 있지 않음. 명령을 찾을 수 없다는 오류가 나옴 |
| uv | `uv --version` | `uv 0.13.1 (62faed335 2026-10-13 x86_64-pc-windows-msvc)` |
| python | `python --version` | `Python` (버전 번호 없음) |
| python | `python3.12 --version` | `Python 3.12.15` |
| python | `uv run --no-project python --version` | `Python 3.12.15` |

- `python` 과 `python3` 명령은 Microsoft Store 연결용 빈 파일(0바이트)이라 실제 Python 이 아니다. 실제 Python 은 uv 가 설치한 3.12.15 이다.
- 이 Python 을 쓸 때는 `python3.12` 나 `uv run` 으로 실행한다.

## 새로 설치한 것
- node v24.22.0 (LTS), npm 11.19.1 — 2026-10-19 설치.
  - winget 설치가 실패(winget 자체 충돌 0xC0000005)해서 nodejs.org 의 zip 을 받아 SHA256 을 확인한 뒤 `%LOCALAPPDATA%\Programs\nodejs` 에 풀고, 사용자 PATH 에 추가했다.
  - 이미 열려 있던 터미널과 VS Code 는 PATH 갱신을 위해 다시 시작해야 한다.

## 아직 설치하지 않은 것
- 없음.
