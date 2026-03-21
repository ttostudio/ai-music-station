# AI Music Station - Liquidsoap channel configuration
# Environment variables are injected by Docker

channel = environment.get("CHANNEL")
icecast_host = environment.get(default="icecast", "ICECAST_HOST")
icecast_port = int_of_string(environment.get(default="8000", "ICECAST_PORT"))
icecast_password = environment.get("ICECAST_SOURCE_PASSWORD")

tracks_dir = "/tracks/#{channel}"
silence_file = "/etc/liquidsoap/silence.flac"

# Fallback: silence
silence = single(silence_file)

# Main playlist: watch the tracks directory for new files
tracks = playlist(
  mode="randomize",
  reload_mode="watch",
  tracks_dir
)

# Crossfade between tracks
radio = crossfade(tracks)

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
