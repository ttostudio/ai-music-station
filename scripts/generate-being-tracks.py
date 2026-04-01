#!/usr/bin/env python3
"""ビーイング系楽曲をACE-Step APIで生成してbeingチャンネルに配置するスクリプト。

使い方:
  python3 scripts/generate-being-tracks.py [--api-url URL] [--count N] [--dry-run]
"""
import argparse
import base64
import json
import os
import sys
import time
from pathlib import Path

import httpx

BEING_TRACKS_DIR = Path(__file__).parent.parent / "generated_tracks" / "being"
PLAYLIST_PATH = BEING_TRACKS_DIR / "playlist.m3u"

# ビーイング系90年代J-POPロック プロンプト
BEING_PROMPTS = [
    {
        "title": "Eternal Breeze",
        "prompt": "90s Japanese pop rock, female vocal, bright and emotional, "
                  "driving guitar riffs, upbeat drums, inspirational melody, "
                  "ZARD style, summer feeling, positive energy, catchy chorus, "
                  "key of D major, 140 bpm",
        "lyrics": "[verse]\n青い空の下 走り出した日々\n風が髪を揺らす あの夏の記憶\n"
                  "[chorus]\n負けないで もう少し\n最後まで走り抜けて\n"
                  "[verse]\n涙の数だけ 強くなれるから\n明日への扉を 今開けよう\n"
                  "[chorus]\n負けないで ほらそこに\nゴールは近づいてる",
    },
    {
        "title": "Burning Soul",
        "prompt": "90s Japanese hard rock, powerful male vocal, heavy guitar, "
                  "intense energy, stadium rock, B'z style, dramatic melody, "
                  "guitar solo, passionate singing, key of E minor, 155 bpm",
        "lyrics": "[verse]\n灼熱の太陽 照りつける道\n俺たちは止まらない このまま\n"
                  "[chorus]\nBurning soul 燃え尽きるまで\n叫び続けろ この声が届くまで\n"
                  "[verse]\n過去の傷跡も 力に変えて\n誰よりも高く 飛んでみせる\n"
                  "[chorus]\nBurning soul 魂を燃やせ\n限界なんてない この手で掴め",
    },
    {
        "title": "Moonlight Serenade",
        "prompt": "90s Japanese pop ballad, smooth male vocal, romantic, "
                  "acoustic guitar and piano, gentle drums, DEEN style, "
                  "emotional love song, nostalgic, key of C major, 80 bpm",
        "lyrics": "[verse]\n月明かりの中 君を想う夜\n遠い記憶が 蘇る\n"
                  "[chorus]\nもう一度 あの日に戻れたら\n伝えきれなかった言葉を\n"
                  "[verse]\n季節は巡り 時は流れても\nこの心だけは 変わらない\n"
                  "[chorus]\nもう一度 君に会えたなら\n今度こそ素直に言えるだろう",
    },
    {
        "title": "Secret Night",
        "prompt": "90s Japanese pop rock, male vocal group, dark and mysterious, "
                  "synth rock, WANDS style, urban night atmosphere, "
                  "driving beat, minor key melody, key of A minor, 130 bpm",
        "lyrics": "[verse]\n夜の街を彷徨い 答えを探してる\nネオンの光が 影を照らす\n"
                  "[chorus]\nSecret night 誰にも見せない\nこの想いを抱えたまま 歩き出す\n"
                  "[verse]\n凍える風の中 君の声が聞こえた\n振り返れば そこに 幻が\n"
                  "[chorus]\nSecret night 闇を切り裂いて\n真実だけを 掴み取りたい",
    },
    {
        "title": "Crystal Sky",
        "prompt": "90s Japanese pop, female vocal, uplifting and bright, "
                  "rock band arrangement, catchy hook, summer anthem, "
                  "being style, positive lyrics, key of G major, 145 bpm",
        "lyrics": "[verse]\nクリスタルの空に 手を伸ばして\n届かないものなど ないと信じて\n"
                  "[chorus]\n走れ 走れ どこまでも\n明日の光を追いかけて\n"
                  "[verse]\n涙を拭いたら また前を向く\n一人じゃないから 大丈夫\n"
                  "[chorus]\n走れ 走れ この道を\n夢の先にある景色を見に行こう",
    },
    {
        "title": "Rainy Blues",
        "prompt": "90s Japanese rock ballad, male vocal, melancholic, "
                  "electric guitar, emotional solo, rain atmosphere, "
                  "T-BOLAN style, heartbreak song, key of F minor, 90 bpm",
        "lyrics": "[verse]\n雨が降り続く 灰色の街\nあの日の約束が 溶けていく\n"
                  "[chorus]\nRainy blues この痛みさえも\nいつか懐かしくなる日が来るのか\n"
                  "[verse]\n壊れた傘を 握りしめたまま\n君がいた場所を ただ見つめてた\n"
                  "[chorus]\nRainy blues 忘れられないなら\nせめてこの歌に 想いを込めて",
    },
]


from typing import Optional

def generate_track(client: httpx.Client, api_url: str, prompt_data: dict, duration: int = 10) -> Optional[bytes]:
    """ACE-Step APIで楽曲を生成し、MP3バイトを返す。"""
    payload = {
        "model": "ACE-Step",
        "messages": [
            {
                "role": "user",
                "content": prompt_data["prompt"],
            }
        ],
        "audio_duration": duration,
        "infer_step": 60,
    }

    # lyrics があればメッセージに追加
    if prompt_data.get("lyrics"):
        payload["messages"][0]["content"] += f"\n\n[lyrics]\n{prompt_data['lyrics']}"

    print(f"  生成中: {prompt_data['title']} (duration={duration}s)...")
    try:
        resp = client.post(
            f"{api_url}/v1/chat/completions",
            json=payload,
            timeout=300.0,  # 5分タイムアウト
        )
        resp.raise_for_status()
        data = resp.json()

        # base64 MP3を抽出
        audio_url = data["choices"][0]["message"]["audio"][0]["audio_url"]["url"]
        if audio_url.startswith("data:audio/mpeg;base64,"):
            b64_data = audio_url.split(",", 1)[1]
            return base64.b64decode(b64_data)
        else:
            print(f"  ⚠ 予期しないaudio_url形式: {audio_url[:50]}...")
            return None

    except httpx.TimeoutException:
        print(f"  ✗ タイムアウト: {prompt_data['title']}")
        return None
    except Exception as e:
        print(f"  ✗ エラー: {prompt_data['title']} — {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="ビーイング系楽曲生成")
    parser.add_argument("--api-url", default="http://localhost:8001", help="ACE-Step API URL")
    parser.add_argument("--count", type=int, default=len(BEING_PROMPTS), help="生成曲数")
    parser.add_argument("--duration", type=int, default=10, help="楽曲長さ(秒)")
    parser.add_argument("--dry-run", action="store_true", help="生成せずプロンプト確認のみ")
    args = parser.parse_args()

    BEING_TRACKS_DIR.mkdir(parents=True, exist_ok=True)

    prompts = BEING_PROMPTS[:args.count]

    if args.dry_run:
        print(f"=== Dry Run: {len(prompts)}曲 ===")
        for p in prompts:
            print(f"  - {p['title']}: {p['prompt'][:80]}...")
        return

    # ACE-Step 接続確認
    try:
        resp = httpx.get(f"{args.api_url}/v1/models", timeout=5.0)
        resp.raise_for_status()
        print(f"ACE-Step API接続OK: {args.api_url}")
    except Exception as e:
        print(f"ACE-Step API接続失敗: {args.api_url} — {e}")
        sys.exit(1)

    client = httpx.Client()
    generated = []

    for i, prompt_data in enumerate(prompts):
        print(f"\n[{i+1}/{len(prompts)}] {prompt_data['title']}")
        mp3_bytes = generate_track(client, args.api_url, prompt_data, args.duration)

        if mp3_bytes:
            filename = f"{prompt_data['title'].lower().replace(' ', '_')}.mp3"
            filepath = BEING_TRACKS_DIR / filename
            filepath.write_bytes(mp3_bytes)
            generated.append(filename)
            print(f"  ✓ 保存: {filepath} ({len(mp3_bytes)} bytes)")
        else:
            print(f"  ✗ スキップ")

        # 連続生成の間隔（メモリ解放のため）
        if i < len(prompts) - 1:
            print("  10秒待機...")
            time.sleep(10)

    # playlist.m3u 更新
    existing = set()
    if PLAYLIST_PATH.exists():
        existing = set(PLAYLIST_PATH.read_text().strip().split("\n")) - {""}

    all_tracks = sorted(existing | set(generated))
    PLAYLIST_PATH.write_text("\n".join(all_tracks) + "\n")

    print(f"\n=== 完了 ===")
    print(f"生成: {len(generated)}/{len(prompts)}曲")
    print(f"playlist.m3u: {len(all_tracks)}曲")


if __name__ == "__main__":
    main()
