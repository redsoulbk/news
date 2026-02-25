# 데일리 한국 주식 뉴스 영상 자동 제작기

어르신 시청자를 위한 **5분 내외 한국 주식 뉴스 영상**을 자동으로 생성합니다.
한 번 실행으로 아래를 같이 만듭니다.

- 한국어 음성(TTS)
- 자막(SRT)
- 슬라이드 기반 애니메이션 영상(MP4)

## 설치

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## 빠른 환경 점검

```bash
python daily_kstock_video.py --check-env
```

> `feedparser`는 더 이상 필요하지 않습니다. RSS는 표준 라이브러리로 파싱합니다.

## 실행

```bash
python daily_kstock_video.py --date 2026-02-25 --limit 6 --outdir outputs
```

생성물:
- `outputs/daily_kstock_news.mp4`
- `outputs/daily_kstock_news.srt`
- `outputs/sources.txt`

## 기본 동작

1. 연합뉴스 RSS에서 증시 관련 제목을 수집합니다.
2. 어르신 눈높이 설명문을 만들어 섹션별 내레이션을 구성합니다.
3. gTTS로 섹션별 음성을 생성합니다.
4. PIL로 만든 텍스트 슬라이드에 줌 애니메이션을 넣어 영상으로 합칩니다.
5. 음성 길이에 맞춘 문장 단위 자막(SRT)을 만듭니다.

## 운영 팁 (매일 자동화)

크론 예시:

```bash
0 18 * * 1-5 cd /workspace/news && /usr/bin/python3 daily_kstock_video.py --date "$(date +\%F)" --outdir outputs
```

## 트러블슈팅

- `ModuleNotFoundError`가 나면, 실행한 파이썬과 같은 인터프리터로 설치하세요.
  - 예: `/path/to/python -m pip install -r requirements.txt`
- 영상 생성은 ffmpeg를 사용하는 moviepy가 필요합니다.
- gTTS 호출 시 인터넷 연결이 필요합니다.

## 주의

- 본 도구는 투자 자문이 아닌 정보 요약 자동화 도구입니다.
