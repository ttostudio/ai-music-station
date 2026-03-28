"""
結合テスト — GET /api/tracks/search（実 DB 接続）
テストID: IT-010〜012
"""
from __future__ import annotations

import time
import uuid

import pytest

from .conftest import insert_test_channel, insert_test_track, _run_sql


@pytest.mark.integration
def test_search_returns_200_real_db(test_client):
    """IT-010: 実 DB で /api/tracks/search が 200 を返す"""
    response = test_client.get("/api/tracks/search")
    assert response.status_code == 200
    data = response.json()
    assert "tracks" in data
    assert "total" in data


@pytest.mark.integration
def test_search_full_text_real_db(test_client):
    """IT-010: 実 DB に複数トラックを INSERT し、q パラメータで絞り込まれることを確認"""
    unique_id = str(uuid.uuid4())[:8]
    track = insert_test_track(f"integtest-lofi-{unique_id}", mood="chill")
    insert_test_track(f"integtest-anime-{unique_id}", mood="energy")

    response = test_client.get(f"/api/tracks/search?q=integtest-lofi-{unique_id}")
    assert response.status_code == 200
    data = response.json()
    titles = [t.get("title") or "" for t in data["tracks"]]
    assert any(f"integtest-lofi-{unique_id}" in t for t in titles), \
        f"挿入したトラックが検索結果に含まれない。results={data['tracks'][:3]}"


@pytest.mark.integration
def test_search_excludes_retired_tracks_real_db(test_client):
    """IT-010b: is_retired=True のトラックが検索結果に含まれない"""
    unique_id = str(uuid.uuid4())[:8]
    ch = insert_test_channel("test-integration")
    _run_sql(f"""
        INSERT INTO tracks (id, channel_id, file_path, caption, title, mood, duration_ms,
            play_count, like_count, is_retired, created_at)
        VALUES ('{uuid.uuid4()}', '{ch["id"]}', '/tracks/retired.mp3',
            'retired caption', 'integtest-retired-{unique_id}', 'chill', 180000,
            0, 0, true, NOW());
    """)

    response = test_client.get(f"/api/tracks/search?q=integtest-retired-{unique_id}")
    assert response.status_code == 200
    data = response.json()
    for t in data["tracks"]:
        assert f"integtest-retired-{unique_id}" not in (t.get("title") or ""), \
            "retired トラックが検索結果に含まれている"


@pytest.mark.integration
def test_search_sort_popular_real_db(test_client):
    """IT-012: sort=popular で実 DB の結果が play_count 降順になる"""
    response = test_client.get("/api/tracks/search?sort=popular")
    assert response.status_code == 200
    data = response.json()
    counts = [t["play_count"] for t in data["tracks"]]
    assert counts == sorted(counts, reverse=True), "play_count が降順でない"


@pytest.mark.integration
def test_search_channel_slug_filter_real_db(test_client):
    """IT-011: channel_slug フィルターが動作する（実 DB）"""
    unique_slug = f"it-slug-{str(uuid.uuid4())[:6]}"
    insert_test_track(f"channel-filter-test", channel_slug=unique_slug)

    response = test_client.get(f"/api/tracks/search?channel_slug={unique_slug}")
    assert response.status_code == 200
    data = response.json()
    for t in data["tracks"]:
        assert t.get("channel_slug") == unique_slug


@pytest.mark.integration
def test_search_response_time_real_db(test_client):
    """NFR-002: search API の応答時間が 300ms 以内"""
    start = time.time()
    response = test_client.get("/api/tracks/search?q=test")
    elapsed = (time.time() - start) * 1000
    assert response.status_code == 200
    assert elapsed < 300, f"応答時間 {elapsed:.0f}ms が 300ms を超過"
