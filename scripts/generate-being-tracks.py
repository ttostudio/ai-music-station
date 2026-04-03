#!/usr/bin/env python3
"""ビーイング系楽曲をACE-Step APIで生成してbeingチャンネルに配置するスクリプト。

使い方:
  python3 scripts/generate-being-tracks.py [--api-url URL] [--count N] [--dry-run]
  python3 scripts/generate-being-tracks.py --channel being --music-api-url http://localhost:3600/api
"""
import argparse
import base64
import json
import os
import random
import re
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
    # --- 追加6曲 (#897) ---
    {
        "title": "Dreams On Fire",
        "prompt": "90s Japanese pop rock, powerful female vocal, passionate, "
                  "brass section and rock band, energetic chorus, "
                  "Okubo Maki style, motivational anthem, key of B flat major, 150 bpm",
        "lyrics": "[verse]\n朝焼けの空に 誓いを立てた\n誰にも負けない 強さが欲しい\n"
                  "[chorus]\nDreams on fire 夢を燃やせ\nどんな壁だって 越えてみせる\n"
                  "[verse]\n転んだ数だけ 立ち上がれるから\nこの手を離さないで\n"
                  "[chorus]\nDreams on fire 心を燃やせ\n最後に笑うのは 私たちだから",
    },
    {
        "title": "Sudden Love",
        "prompt": "90s Japanese pop, bright female vocal duo, catchy pop melody, "
                  "synth and guitar, dance beat, MANISH style, "
                  "love song, cheerful energy, key of E major, 135 bpm",
        "lyrics": "[verse]\n突然の出会いに 胸が高鳴る\n運命なんて 信じてなかったのに\n"
                  "[chorus]\nSudden love 恋に落ちた\nこの気持ちは もう止められない\n"
                  "[verse]\n笑顔の裏に 隠した想い\n今日こそ伝えたい\n"
                  "[chorus]\nSudden love 素直になれたら\nきっと世界は もっと輝くから",
    },
    {
        "title": "Wind Chaser",
        "prompt": "90s Japanese rock, energetic male vocal, punk rock influence, "
                  "fast guitar, driving rhythm, BAAD style, "
                  "youth anthem, rebellious spirit, key of A major, 165 bpm",
        "lyrics": "[verse]\n風を追いかけて 走り出した午後\nルールなんか 知らない\n"
                  "[chorus]\nWind chaser 自由を掴め\n誰かの真似じゃない 俺の道を行く\n"
                  "[verse]\n退屈な毎日 蹴り飛ばして\n本当の自分を 探しに行こう\n"
                  "[chorus]\nWind chaser 風になれ\nこの街を飛び出せ 今すぐに",
    },
    {
        "title": "Diamond Ocean",
        "prompt": "90s Japanese pop rock, melodic male vocal, anthemic rock, "
                  "soaring guitar melody, Oda Tetsuro style, "
                  "ocean and freedom imagery, epic arrangement, key of D major, 140 bpm",
        "lyrics": "[verse]\nダイヤモンドの海に 船を出そう\n地図にない場所を 目指して\n"
                  "[chorus]\n輝く波の向こうに 未来がある\nDiamond ocean 漕ぎ出せ\n"
                  "[verse]\n嵐が来ても 錨を上げろ\n信じた道は 間違いじゃない\n"
                  "[chorus]\n輝く波の彼方に 夢がある\nDiamond ocean 止まるな",
    },
    {
        "title": "Starlight Memory",
        "prompt": "90s Japanese pop, gentle female vocal, nostalgic ballad, "
                  "piano and strings, soft rock arrangement, "
                  "Komatsu Miho style, bittersweet love, key of F major, 85 bpm",
        "lyrics": "[verse]\n星降る夜に 思い出すのは\nあなたと過ごした 短い季節\n"
                  "[chorus]\nStarlight memory 消えないで\nあの日の約束 まだ覚えてる\n"
                  "[verse]\n手紙を書いては 破り捨てた\n素直になれない 自分が嫌で\n"
                  "[chorus]\nStarlight memory 輝いて\nいつかまた会える日を 信じてる",
    },
    {
        "title": "Brave Heart Rising",
        "prompt": "90s Japanese pop rock, male vocal, FIELD OF VIEW style, "
                  "dramatic build-up, soaring chorus, rock ballad, "
                  "emotional guitar, inspirational, key of C major, 125 bpm",
        "lyrics": "[verse]\n突然の別れに 立ち尽くした\n何も見えない 暗闇の中\n"
                  "[chorus]\nBrave heart rising 立ち上がれ\nまだ終わりじゃない この物語は\n"
                  "[verse]\n傷ついた翼で それでも飛べる\n信じる心が あれば\n"
                  "[chorus]\nBrave heart rising 夜明けを待て\n必ず来る 新しい朝が",
    },
]


from typing import Optional


def validate_slug(slug: str) -> bool:
    return bool(re.match(r'^[a-z0-9_-]+$', slug))


def fetch_channel_config(music_api_url: str, channel_slug: str) -> dict | None:
    try:
        resp = httpx.get(f"{music_api_url.rstrip('/')}/channels/{channel_slug}", timeout=5.0)
        resp.raise_for_status()
        data = resp.json()
        return {"min_duration": data.get("min_duration", 180), "max_duration": data.get("max_duration", 600)}
    except Exception as e:
        print(f"⚠ チャンネル設定取得失敗（フォールバック使用）: {e}")
        return None


def generate_track(client: httpx.Client, api_url: str, prompt_data: dict, duration: int = 10) -> Optional[bytes]:
    """ACE-Step APIで楽曲を生成し、MP3バイトを返す。/release_task API使用（use_tiled_decode=false必須）。

    query_result API仕様:
      - パラメータ: task_id_list (list of task_id strings)
      - レスポンス status: 0=running, 1=succeeded, 2=failed
      - 成功時: result JSON内の file フィールドにローカルファイルパス
    """
    payload = {
        "prompt": prompt_data["prompt"],
        "lyrics": prompt_data.get("lyrics", ""),
        "audio_duration": duration,
        "audio_format": "mp3",
        "use_tiled_decode": False,
    }

    print(f"  生成中: {prompt_data['title']} (duration={duration}s)...")
    try:
        resp = client.post(
            f"{api_url}/release_task",
            json=payload,
            timeout=30.0,
        )
        resp.raise_for_status()
        task_data = resp.json()
        job_id = task_data.get("data", {}).get("task_id") or task_data.get("data", {}).get("job_id")
        if not job_id:
            print(f"  ✗ task_id取得失敗: {task_data}")
            return None

        print(f"  ジョブ投入: {job_id}")

        # duration に応じてタイムアウトを調整（240s楽曲は生成に10分以上かかりうる）
        max_polls = max(120, duration * 2)
        for poll_i in range(max_polls):
            time.sleep(5)
            poll = client.post(
                f"{api_url}/query_result",
                json={"task_id_list": [job_id]},
                timeout=10.0,
            )
            poll.raise_for_status()
            result = poll.json()
            data = result.get("data", [])
            if not data:
                continue
            job = data[0]
            status_code = job.get("status", 0)

            if status_code == 1:  # succeeded
                # result は JSON文字列でラップされている
                result_str = job.get("result", "[]")
                try:
                    result_items = json.loads(result_str) if isinstance(result_str, str) else result_str
                except json.JSONDecodeError:
                    result_items = []
                if not result_items:
                    print(f"  ⚠ 成功だがresultが空")
                    return None
                file_field = result_items[0].get("file", "") if isinstance(result_items, list) else ""
                if not file_field:
                    print(f"  ⚠ fileフィールドが空")
                    return None
                # file_field は /v1/audio?path=... 形式のURLパス
                # URLパースしてpathパラメータからローカルファイルパスを抽出
                if file_field.startswith("/v1/audio"):
                    from urllib.parse import urlparse, parse_qs, unquote
                    parsed = urlparse(file_field)
                    qs = parse_qs(parsed.query)
                    local_path = unquote(qs.get("path", [""])[0])
                    if local_path and os.path.exists(local_path):
                        print(f"  ✓ 生成完了: {local_path}")
                        return Path(local_path).read_bytes()
                    else:
                        # HTTP経由で取得を試みる
                        audio_url = f"{api_url}{file_field}"
                        print(f"  ローカルパス不在、HTTP取得: {audio_url[:80]}")
                        audio_resp = client.get(audio_url, timeout=30.0)
                        if audio_resp.status_code == 200:
                            return audio_resp.content
                        print(f"  ⚠ HTTP取得失敗: {audio_resp.status_code}")
                        return None
                elif os.path.exists(file_field):
                    print(f"  ✓ 生成完了: {file_field}")
                    return Path(file_field).read_bytes()
                else:
                    print(f"  ⚠ ファイルが見つからない: {file_field}")
                    return None
            elif status_code == 2:  # failed
                result_str = job.get("result", "[]")
                print(f"  ✗ 生成失敗: {result_str[:200]}")
                return None
            # status_code == 0: still running
            if poll_i > 0 and poll_i % 12 == 0:
                progress = job.get("progress_text", "")
                print(f"    ... まだ処理中 ({poll_i * 5}s経過) {progress[:80]}")

        print(f"  ✗ タイムアウト（{max_polls * 5}秒）")
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
    parser.add_argument("--min-duration", type=int, default=180, help="最小楽曲長さ(秒)")
    parser.add_argument("--max-duration", type=int, default=600, help="最大楽曲長さ(秒)")
    parser.add_argument("--dry-run", action="store_true", help="生成せずプロンプト確認のみ")
    parser.add_argument("--channel", default="being", help="チャンネルslug")
    parser.add_argument("--music-api-url", default="http://localhost:3600/api", help="Music Station API URL")
    args = parser.parse_args()

    # channel_slug バリデーション
    if not validate_slug(args.channel):
        print(f"✗ 無効なチャンネルslug: {args.channel}")
        sys.exit(1)

    # チャンネル設定取得（dry-run でも実行）
    config = fetch_channel_config(args.music_api_url, args.channel)
    if config:
        min_dur = config["min_duration"]
        max_dur = config["max_duration"]
        print(f"チャンネル設定取得: duration={min_dur}-{max_dur}s")
    else:
        min_dur = args.min_duration
        max_dur = args.max_duration
        print(f"フォールバック: duration={min_dur}-{max_dur}s")

    BEING_TRACKS_DIR.mkdir(parents=True, exist_ok=True)

    prompts = BEING_PROMPTS[:args.count]

    if args.dry_run:
        print(f"=== Dry Run: {len(prompts)}曲 (duration={min_dur}-{max_dur}s) ===")
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
        duration = random.randint(min_dur, max_dur)
        mp3_bytes = generate_track(client, args.api_url, prompt_data, duration)

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
