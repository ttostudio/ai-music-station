-- AI Music Station デフォルトチャンネルのシードデータ
-- Alembic マイグレーションで自動実行、または手動で実行可能

INSERT INTO channels (slug, name, description, is_active, default_bpm_min, default_bpm_max, default_duration, default_key, default_instrumental, prompt_template, vocal_language)
VALUES
  ('lofi', 'LoFi ビーツ', 'リラックス＆勉強用のチルなローファイ・ヒップホップ', true, 70, 90, 180, 'Cm', true, 'lo-fi hip hop beat, chill, relaxed, vinyl crackle, mellow piano, ambient pads, soft drums, warm bass, nostalgic, cozy atmosphere', NULL),
  ('anime', 'アニソン', 'AIが生成したアニメのオープニング＆エンディングテーマ', true, 120, 160, 90, 'C', false, 'anime opening theme, energetic, J-pop, catchy melody, orchestral arrangement, electric guitar, powerful vocals, dramatic, uplifting, epic chorus', 'ja'),
  ('jazz', 'ジャズステーション', 'スムースジャズ、即興演奏、クラシックな雰囲気', true, 100, 140, 240, NULL, true, 'jazz, smooth, saxophone solo, piano comping, upright bass walking, brush drums, improvisational, warm tone, sophisticated harmony, swing feel, late night jazz club atmosphere', NULL)
ON CONFLICT (slug) DO NOTHING;
