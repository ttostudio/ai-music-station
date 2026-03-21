-- Seed default channels for AI Music Station
-- This runs automatically via Alembic or can be executed manually

INSERT INTO channels (slug, name, description, is_active, default_bpm_min, default_bpm_max, default_duration, default_key, default_instrumental, prompt_template, vocal_language)
VALUES
  ('lofi', 'LoFi Beats', 'Chill lo-fi hip hop beats to relax and study to', true, 70, 90, 180, 'Cm', true, 'lo-fi hip hop beat, chill, relaxed, vinyl crackle, mellow piano, ambient pads, soft drums, warm bass, nostalgic, cozy atmosphere', NULL),
  ('anime', 'Anime Songs', 'AI-generated anime opening and ending themes', true, 120, 160, 90, 'C', false, 'anime opening theme, energetic, J-pop, catchy melody, orchestral arrangement, electric guitar, powerful vocals, dramatic, uplifting, epic chorus', 'ja'),
  ('jazz', 'Jazz Station', 'Smooth jazz, improvisation, and classic vibes', true, 100, 140, 240, NULL, true, 'jazz, smooth, saxophone solo, piano comping, upright bass walking, brush drums, improvisational, warm tone, sophisticated harmony, swing feel, late night jazz club atmosphere', NULL)
ON CONFLICT (slug) DO NOTHING;
