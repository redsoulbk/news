#!/usr/bin/env python3
"""어르신 대상 한국 주식 뉴스 5분 영상 자동 제작기."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import importlib
import os
import re
import sys
import textwrap
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

RSS_FEEDS = [
    "https://www.yna.co.kr/rss/finance.xml",
    "https://www.yna.co.kr/rss/economy.xml",
]


@dataclass
class NewsItem:
    title: str
    link: str
    source: str


@dataclass
class Segment:
    title: str
    narration: str


def clean_text(value: str) -> str:
    value = html.unescape(value or "")
    value = re.sub(r"<[^>]+>", "", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def fetch_news(limit: int = 6) -> List[NewsItem]:
    """feedparser 없이 표준 라이브러리로 RSS 파싱."""
    items: list[NewsItem] = []
    for feed_url in RSS_FEEDS:
        try:
            with urllib.request.urlopen(feed_url, timeout=10) as resp:
                xml_bytes = resp.read()
            root = ET.fromstring(xml_bytes)
        except Exception:
            continue

        for node in root.findall(".//item")[: limit * 3]:
            title = clean_text(node.findtext("title", default=""))
            link = clean_text(node.findtext("link", default=""))
            source = clean_text(node.findtext("source", default="연합뉴스")) or "연합뉴스"
            if not title:
                continue
            if all(keyword not in title for keyword in ("주식", "증시", "코스피", "코스닥", "상장")):
                continue
            items.append(NewsItem(title=title, link=link, source=source))

    unique: list[NewsItem] = []
    seen = set()
    for item in items:
        if item.title in seen:
            continue
        seen.add(item.title)
        unique.append(item)
        if len(unique) >= limit:
            break
    return unique


def make_senior_friendly_segments(news_items: Iterable[NewsItem], date_text: str) -> List[Segment]:
    intro = Segment(
        title="오늘의 한국 주식 뉴스",
        narration=(
            f"안녕하세요. {date_text} 한국 주식 시장 소식을 쉽게 정리해드립니다. "
            "어르신 눈높이에 맞춰 핵심만 천천히 설명드릴게요."
        ),
    )

    body: list[Segment] = []
    for idx, item in enumerate(news_items, start=1):
        narration = (
            f"{idx}번째 소식입니다. {item.title}. "
            "이 소식이 시장에 주는 의미는 관련 업종 투자 심리에 영향을 줄 수 있다는 점입니다. "
            "하루 이슈만 보고 급하게 매수하기보다 분할매수와 위험관리 원칙을 지켜주세요."
        )
        body.append(Segment(title=f"뉴스 {idx}", narration=narration))

    market_tip = Segment(
        title="오늘의 안전 투자 한마디",
        narration=(
            "생활자금과 투자자금은 꼭 분리하세요. "
            "한 종목에 몰빵하기보다 ETF 등 분산투자를 고려하면 변동성을 줄이는 데 도움이 됩니다. "
            "오늘도 무리하지 않는 투자 하시길 바랍니다."
        ),
    )

    outro = Segment(
        title="마무리",
        narration=(
            "지금까지 오늘의 한국 주식 뉴스였습니다. "
            "도움이 되셨다면 내일도 같은 시간에 찾아뵙겠습니다."
        ),
    )

    return [intro, *body, market_tip, outro]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def load_media_deps():
    """런타임 시점에만 외부 의존성 import (실패 시 친절한 메시지)."""
    missing = []
    for module in ("gtts", "moviepy.editor", "PIL"):
        try:
            importlib.import_module(module)
        except Exception:
            missing.append(module)

    if missing:
        modules = ", ".join(missing)
        raise RuntimeError(
            "필수 패키지가 없습니다: "
            f"{modules}.\n"
            "같은 파이썬 인터프리터로 아래를 실행하세요:\n"
            f"  {sys.executable} -m pip install -r requirements.txt"
        )

    from gtts import gTTS
    from moviepy.editor import AudioFileClip, CompositeVideoClip, ImageClip, concatenate_videoclips
    from PIL import Image, ImageDraw, ImageFont

    return gTTS, AudioFileClip, CompositeVideoClip, ImageClip, concatenate_videoclips, Image, ImageDraw, ImageFont


def pick_font(ImageFont, font_size: int):
    font_candidates = [
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for candidate in font_candidates:
        if os.path.exists(candidate):
            return ImageFont.truetype(candidate, font_size)
    return ImageFont.load_default()


def draw_slide(Image, ImageDraw, ImageFont, title: str, narration: str, out_path: Path, size: tuple[int, int] = (1280, 720)) -> None:
    width, height = size
    image = Image.new("RGB", size, color=(13, 27, 42))
    draw = ImageDraw.Draw(image)

    title_font = pick_font(ImageFont, 54)
    body_font = pick_font(ImageFont, 36)

    draw.rectangle((50, 40, width - 50, 140), fill=(27, 38, 59))
    draw.text((80, 65), title, fill=(255, 214, 10), font=title_font)

    wrapped = textwrap.fill(narration, width=34)
    draw.multiline_text((80, 190), wrapped, fill=(240, 240, 240), font=body_font, spacing=14)

    draw.rectangle((50, height - 90, width - 50, height - 40), fill=(65, 90, 119))
    draw.text((80, height - 80), "※ 본 영상은 투자 판단 참고용이며, 투자 손실의 책임은 투자자 본인에게 있습니다.", fill=(255, 255, 255), font=pick_font(ImageFont, 26))

    image.save(out_path)


def split_sentences(text: str) -> List[str]:
    parts = re.split(r"(?<=[.!?다요])\s+", text)
    cleaned = [p.strip() for p in parts if p.strip()]
    return cleaned if cleaned else [text]


def generate_srt(AudioFileClip, segments: List[Segment], audio_paths: List[Path], out_path: Path) -> None:
    cursor = 0.0
    idx = 1
    lines: list[str] = []

    def ts(sec: float) -> str:
        ms = int((sec - int(sec)) * 1000)
        base = int(sec)
        s = base % 60
        m = (base // 60) % 60
        h = base // 3600
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    for seg, audio_path in zip(segments, audio_paths):
        audio = AudioFileClip(str(audio_path))
        duration = float(audio.duration)
        audio.close()

        sentences = split_sentences(seg.narration)
        total_chars = sum(len(s) for s in sentences) or 1
        local = 0.0
        for sentence in sentences:
            part = duration * len(sentence) / total_chars
            start = cursor + local
            end = start + part
            lines.extend([str(idx), f"{ts(start)} --> {ts(end)}", sentence, ""])
            idx += 1
            local += part
        cursor += duration

    out_path.write_text("\n".join(lines), encoding="utf-8")


def build_video(segments: List[Segment], workdir: Path, output_mp4: Path, fps: int = 24) -> None:
    gTTS, AudioFileClip, CompositeVideoClip, ImageClip, concatenate_videoclips, Image, ImageDraw, ImageFont = load_media_deps()

    clips = []
    audio_paths: list[Path] = []

    for i, seg in enumerate(segments, start=1):
        slide_path = workdir / f"slide_{i:02d}.png"
        audio_path = workdir / f"audio_{i:02d}.mp3"

        draw_slide(Image, ImageDraw, ImageFont, seg.title, seg.narration, slide_path)
        gTTS(text=seg.narration, lang="ko").save(str(audio_path))

        audio = AudioFileClip(str(audio_path))
        dur = max(float(audio.duration), 2.0)
        base = ImageClip(str(slide_path), duration=dur).set_audio(audio)
        animated = base.resize(lambda t: 1.0 + 0.03 * (t / dur)).set_position("center")
        composed = CompositeVideoClip([animated], size=(1280, 720)).fadein(0.3).fadeout(0.3)

        clips.append(composed)
        audio_paths.append(audio_path)

    final = concatenate_videoclips(clips, method="compose")
    final.write_videofile(str(output_mp4), fps=fps, codec="libx264", audio_codec="aac", threads=4, preset="medium")
    final.close()

    for clip in clips:
        clip.close()

    generate_srt(AudioFileClip, segments, audio_paths, output_mp4.with_suffix(".srt"))


def check_env() -> int:
    print(f"python: {sys.executable}")
    required = ["gtts", "moviepy.editor", "PIL"]
    ok = True
    for module in required:
        try:
            importlib.import_module(module)
            print(f"[OK] {module}")
        except Exception:
            ok = False
            print(f"[MISS] {module}")

    print("[INFO] feedparser는 더 이상 필요하지 않습니다 (표준 라이브러리 RSS 파싱 사용).")
    if not ok:
        print(f"설치 명령: {sys.executable} -m pip install -r requirements.txt")
        return 1
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="데일리 한국 주식 뉴스 영상 자동 생성")
    parser.add_argument("--date", default=dt.date.today().isoformat(), help="방송 날짜 (YYYY-MM-DD)")
    parser.add_argument("--limit", type=int, default=6, help="뉴스 아이템 수")
    parser.add_argument("--outdir", default="outputs", help="산출물 폴더")
    parser.add_argument("--filename", default="daily_kstock_news.mp4", help="결과 영상 파일명")
    parser.add_argument("--check-env", action="store_true", help="실행환경 점검만 수행")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.check_env:
        raise SystemExit(check_env())

    outdir = Path(args.outdir)
    ensure_dir(outdir)
    workdir = outdir / "tmp"
    ensure_dir(workdir)

    news_items = fetch_news(limit=args.limit)
    if not news_items:
        news_items = [
            NewsItem(
                title="오늘은 주요 증시 이슈가 제한적이어서, 시장 변동성 관리가 중요하다는 점을 점검합니다",
                link="",
                source="내부 생성",
            )
        ]

    segments = make_senior_friendly_segments(news_items, args.date)
    output_mp4 = outdir / args.filename

    build_video(segments, workdir, output_mp4)

    sources = outdir / "sources.txt"
    source_lines = [f"- {item.title} ({item.source}) {item.link}" for item in news_items]
    sources.write_text("\n".join(source_lines), encoding="utf-8")

    print(f"완료: {output_mp4}")
    print(f"자막: {output_mp4.with_suffix('.srt')}")
    print(f"출처: {sources}")


if __name__ == "__main__":
    main()
