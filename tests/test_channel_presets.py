from worker.channel_presets import PRESETS, all_presets, get_preset


class TestChannelPresets:
    def test_required_channels_exist(self):
        assert "lofi" in PRESETS
        assert "anime" in PRESETS
        assert "jazz" in PRESETS

    def test_all_presets_returns_list(self):
        presets = all_presets()
        assert len(presets) == 3

    def test_get_preset_returns_correct(self):
        preset = get_preset("lofi")
        assert preset is not None
        assert preset.slug == "lofi"
        assert preset.name == "LoFi ビーツ"

    def test_get_preset_returns_none_for_unknown(self):
        assert get_preset("nonexistent") is None

    def test_all_presets_have_required_fields(self):
        for slug, preset in PRESETS.items():
            assert preset.slug == slug
            assert preset.name, f"{slug} missing name"
            assert preset.description, f"{slug} missing description"
            assert preset.bpm_min > 0, f"{slug} invalid bpm_min"
            assert preset.bpm_max >= preset.bpm_min, f"{slug} bpm_max < bpm_min"
            assert preset.duration > 0, f"{slug} invalid duration"
            assert preset.prompt_template, f"{slug} missing prompt_template"

    def test_lofi_is_instrumental(self):
        preset = get_preset("lofi")
        assert preset is not None
        assert preset.instrumental is True
        assert preset.vocal_language is None

    def test_anime_has_japanese_vocals(self):
        preset = get_preset("anime")
        assert preset is not None
        assert preset.instrumental is False
        assert preset.vocal_language == "ja"

    def test_jazz_is_instrumental(self):
        preset = get_preset("jazz")
        assert preset is not None
        assert preset.instrumental is True

    def test_bpm_ranges_are_reasonable(self):
        for slug, preset in PRESETS.items():
            assert 30 <= preset.bpm_min <= 300, f"{slug} bpm_min out of range"
            assert 30 <= preset.bpm_max <= 300, f"{slug} bpm_max out of range"
