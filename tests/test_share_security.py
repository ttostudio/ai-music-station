"""共有機能のセキュリティテスト"""
from __future__ import annotations

from api.routers.shares import _escape_html, _hash_ip


class TestIpHashing:
    def test_ip_hash_is_not_raw_ip(self):
        result = _hash_ip("192.168.1.1")
        assert result != "192.168.1.1"
        assert len(result) == 64  # SHA-256 hex digest

    def test_same_ip_produces_same_hash(self):
        assert _hash_ip("10.0.0.1") == _hash_ip("10.0.0.1")

    def test_different_ips_produce_different_hashes(self):
        assert _hash_ip("10.0.0.1") != _hash_ip("10.0.0.2")


class TestHtmlEscape:
    def test_escapes_script_tags(self):
        assert _escape_html("<script>") == "&lt;script&gt;"

    def test_escapes_quotes(self):
        assert _escape_html('"hello"') == "&quot;hello&quot;"

    def test_escapes_ampersand(self):
        assert _escape_html("a&b") == "a&amp;b"

    def test_preserves_safe_text(self):
        assert _escape_html("Hello World 123") == "Hello World 123"

    def test_escapes_combined_xss(self):
        result = _escape_html('<img src="x" onerror="alert(1)">')
        assert "<" not in result
        assert '"' not in result
