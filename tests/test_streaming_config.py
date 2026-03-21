from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

STREAMING_DIR = Path(__file__).parent.parent / "streaming"
LIQUIDSOAP_DIR = STREAMING_DIR / "liquidsoap"


class TestIcecastConfig:
    @pytest.fixture
    def icecast_xml(self):
        return STREAMING_DIR / "icecast.xml"

    def test_icecast_xml_exists(self, icecast_xml):
        assert icecast_xml.exists()

    def test_icecast_xml_parses(self, icecast_xml):
        tree = ET.parse(icecast_xml)
        root = tree.getroot()
        assert root.tag == "icecast"

    def test_listen_port_is_8000(self, icecast_xml):
        tree = ET.parse(icecast_xml)
        port = tree.find(".//listen-socket/port")
        assert port is not None
        assert port.text == "8000"

    def test_has_cors_header(self, icecast_xml):
        tree = ET.parse(icecast_xml)
        headers = tree.findall(".//http-headers/header")
        cors_found = any(
            h.get("name") == "Access-Control-Allow-Origin"
            for h in headers
        )
        assert cors_found, "CORS header missing"

    def test_has_authentication_section(self, icecast_xml):
        tree = ET.parse(icecast_xml)
        auth = tree.find(".//authentication")
        assert auth is not None
        assert tree.find(".//authentication/source-password") is not None
        assert tree.find(".//authentication/admin-password") is not None


class TestLiquidsoapConfig:
    """統合Liquidsoapの設定テスト（動的生成方式）"""

    def test_no_static_channel_liq(self):
        """channel.liq は動的生成に置換されたため存在しないこと"""
        assert not (LIQUIDSOAP_DIR / "channel.liq").exists()

    def test_entrypoint_generates_dynamic_config(self):
        """entrypoint.sh がAPIからチャンネル取得→動的設定生成すること"""
        content = (LIQUIDSOAP_DIR / "entrypoint.sh").read_text()
        assert "API_BASE_URL" in content
        assert "/api/channels" in content
        assert "radio.liq" in content

    def test_entrypoint_has_icecast_output(self):
        """entrypoint.sh の動的生成にicecast出力設定が含まれること"""
        content = (LIQUIDSOAP_DIR / "entrypoint.sh").read_text()
        assert "output.icecast" in content
        assert "ICECAST_SOURCE_PASSWORD" in content

    def test_entrypoint_has_fallback_and_crossfade(self):
        """entrypoint.sh の動的生成にfallbackとcrossfadeが含まれること"""
        content = (LIQUIDSOAP_DIR / "entrypoint.sh").read_text()
        assert "fallback" in content
        assert "crossfade" in content
        assert "silence" in content

    def test_entrypoint_converts_hyphen_to_underscore(self):
        """slug中のハイフンをアンダースコアに変換すること"""
        content = (LIQUIDSOAP_DIR / "entrypoint.sh").read_text()
        assert "tr '-' '_'" in content

    def test_silence_wav_exists(self):
        assert (LIQUIDSOAP_DIR / "silence.wav").exists()

    def test_entrypoint_exists_and_has_liquidsoap(self):
        entrypoint = LIQUIDSOAP_DIR / "entrypoint.sh"
        assert entrypoint.exists()
        content = entrypoint.read_text()
        assert "liquidsoap" in content


class TestDockerfiles:
    def test_icecast_dockerfile_exists(self):
        assert (STREAMING_DIR / "Dockerfile.icecast").exists()

    def test_liquidsoap_dockerfile_exists(self):
        assert (LIQUIDSOAP_DIR / "Dockerfile").exists()

    def test_icecast_dockerfile_exposes_8000(self):
        content = (STREAMING_DIR / "Dockerfile.icecast").read_text()
        assert "EXPOSE 8000" in content

    def test_liquidsoap_dockerfile_has_entrypoint(self):
        content = (LIQUIDSOAP_DIR / "Dockerfile").read_text()
        assert "entrypoint.sh" in content

    def test_liquidsoap_dockerfile_installs_python3(self):
        """動的チャンネル取得にpython3が必要"""
        content = (LIQUIDSOAP_DIR / "Dockerfile").read_text()
        assert "python3" in content
