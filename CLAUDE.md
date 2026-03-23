# AI Music Station — CLAUDE.md

## ⚠️ 変更禁止ファイル（ttoClawが修正・検証済み）

以下のファイルはttoClawが直接修正・検証済み。**絶対に上書き・リバートしてはいけない。**
変更が必要な場合はttoClaw経由でttoに確認すること。

### streaming/liquidsoap/Dockerfile
- `apt-get install` に **ffmpeg を含めない**（liquidsoap v2.3.2 の内蔵ffmpegと互換性がなく Fatal error になる）
- silence.wav は **そのままCOPY**（flac変換しない）
```dockerfile
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl python3 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*
COPY silence.wav /etc/liquidsoap/silence.wav
```

### streaming/liquidsoap/entrypoint.sh
- silence_file は **`/etc/liquidsoap/silence.wav`**（.flacではない）
- **crossfade を使わない**（再生が10秒で止まるバグの原因）
- playlist は **`mode="randomize", reload=10`** で m3u ファイルのみ参照
```
${var}_radio = playlist(mode="randomize", reload=10, "/tracks/${ch}/playlist.m3u")
${var}_radio = fallback(track_sensitive=false, [${var}_radio, silence])
```

### frontend/src/components/AudioVisualizer.tsx
- `resumeAudioContext()` をexportしている — 削除禁止
- `source.connect(ctx.destination)` で音声出力を直接接続 — 削除禁止
- `audio.crossOrigin = "anonymous"` — CORS対応に必要

### frontend/src/components/Player.tsx
- `crossOrigin="anonymous"` — 削除禁止（別マシンからのアクセスで必要）
- `preload="auto"` — `preload="none"` に戻さない

### frontend/src/App.tsx
- `resumeAudioContext(audioRef.current)` を play 時に呼ぶ — 削除禁止（AudioContext suspended 対策）

### frontend/src/styles.css
- `.album-art-inner` と `.album-art-center` に `pointer-events: none` — 削除禁止（再生ボタンのクリックが効かなくなる）

### caddy/Caddyfile
- `/stream/*` に CORS ヘッダー (`Access-Control-Allow-Origin: *`) — 削除禁止

## 理由
これらは全て、ttoが実際にブラウザで確認して動作検証済みの修正。
元に戻すと「音が出ない」「ラジオが起動しない」「再生ボタンが効かない」等の致命的バグが再発する。
