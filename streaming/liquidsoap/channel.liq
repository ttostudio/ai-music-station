# AI Music Station - Liquidsoap channel configuration
# Environment variables are injected by Docker

channel = environment.get("CHANNEL")
icecast_host = environment.get(default="icecast", "ICECAST_HOST")
icecast_port = int_of_string(environment.get(default="8000", "ICECAST_PORT"))
icecast_password = environment.get("ICECAST_SOURCE_PASSWORD")

tracks_dir = "/tracks/#{channel}"
playlist_file = "/tracks/#{channel}/playlist.m3u"
silence_file = "/etc/liquidsoap/silence.flac"

# Fallback: silence
silence = single(silence_file)

# 重み付きプレイリスト（worker が生成・更新する playlist.m3u）
tracks = playlist(
  mode="normal",
  reload_mode="watch",
  playlist_file
)

# ディレクトリ全体のランダム再生（プレイリスト未生成時のフォールバック）
dir_tracks = playlist(
  mode="randomize",
  reload_mode="watch",
  tracks_dir
)

# プレイリスト優先、なければディレクトリ再生にフォールバック
radio = crossfade(fallback(track_sensitive=true, [tracks, dir_tracks]))

# Use silence as fallback when no tracks exist
radio = fallback(track_sensitive=true, [radio, silence])

# Output to Icecast as OGG Vorbis
output.icecast(
  %vorbis(quality=0.5),
  host=icecast_host,
  port=icecast_port,
  password=icecast_password,
  mount="/#{channel}.ogg",
  name="AI Music Station - #{channel}",
  description="AI-generated music stream",
  radio
)
