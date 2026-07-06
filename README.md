# 주식 시세 추적 (Stock Tracker)

미국·일본 주식 관심종목을 등록하면 하루 2회 자동 수집된 시세를 로컬 대시보드에서 확인하는 개인용 앱.

## 구조

- `collector/` — GitHub Actions가 실행하는 수집 스크립트 (yfinance)
- `data/` — 수집된 시세/환율(공개, git 커밋됨) + `tickers.json`(수집 대상 심볼 목록)
- `backend/` — 로컬에서 실행하는 FastAPI 서버. 관심종목/목표가/알림 확인 상태는 `backend/data/config.local.json`에만 저장(git 미포함)
- `frontend/` — 로컬에서 실행하는 Vite+React 대시보드

시세 데이터는 GitHub Actions(하루 2회, 07:00/16:00 KST)가 수집해 이 리포에 커밋합니다.
로컬 백엔드는 raw.githubusercontent.com에서 항상 최신 데이터를 읽어오므로 별도 `git pull` 없이도 최신 상태를 봅니다.
종목 추가/삭제 시에는 로컬 백엔드가 `data/tickers.json`을 직접 커밋+푸시합니다(로컬에 설정된 git 자격 증명 사용).

## 로컬 실행

### 최초 1회

```bash
cd backend
python -m venv ../.venv       # 또는 원하는 방식으로 가상환경 구성
../.venv/Scripts/python -m pip install -r requirements.txt
```

```bash
cd frontend
npm install
```

### 매번 실행

터미널 1 (백엔드):
```bash
cd backend
../.venv/Scripts/python -m uvicorn main:app --port 8000
```

터미널 2 (프론트엔드):
```bash
cd frontend
npm run dev
```

브라우저에서 http://localhost:5173 접속.

### 수집 스크립트 수동 실행 (테스트용)

```bash
.venv/Scripts/python collector/collect.py
```

## GitHub Actions 상태 확인

리포의 **Actions** 탭에서 `Collect stock prices` 워크플로 실행 이력을 확인할 수 있습니다.
수동으로 1회 실행하려면 Actions 탭 → `Collect stock prices` → `Run workflow` 버튼을 사용하세요.

## 참고

- yfinance는 비공식 라이브러리라 장애가 생길 수 있습니다. 개별 종목 수집이 실패해도 다른 종목과 환율 수집은 계속 진행됩니다.
- 히스토리 데이터는 git 커밋 로그 자체가 보관소이므로 별도 만료 로직이 없습니다.
- 엔화 환산은 100엔 기준(`jpykrw100`)으로 저장/표시합니다.
