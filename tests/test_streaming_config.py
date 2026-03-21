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
    def test_channel_liq_exists(self):
        assert (LIQUIDSOAP_DIR / "channel.liq").exists()

    def test_channel_liq_references_icecast(self):
        content = (LIQUIDSOAP_DIR / "channel.liq").read_text()
        assert "output.icecast" in content
        assert "ICECAST_SOURCE_PASSWORD" in content

    def test_channel_liq_uses_channel_env(self):
        content = (LIQUIDSOAP_DIR / "channel.liq").read_text()
        assert 'environment.get("CHANNEL")' in content

    def test_channel_liq_has_fallback(self):
        content = (LIQUIDSOAP_DIR / "channel.liq").read_text()
        assert "fallback" in content
        assert "silence" in content

    def test_channel_liq_has_crossfade(self):
        content = (LIQUIDSOAP_DIR / "channel.liq").read_text()
        assert "crossfade" in content

    def test_silence_wav_exists(self):
        assert (LIQUIDSOAP_DIR / "silence.wav").exists()

    def test_entrypoint_exists_and_executable_content(self):
        entrypoint = LIQUIDSOAP_DIR / "entrypoint.sh"
        assert entrypoint.exists()
        content = entrypoint.read_text()
        assert "CHANNEL" in content
        assert "liquidsoap" in content


class TestDockerfiles:
    def test_icecast_dockerfile_exists(self):
        assert (STREAMING_DIR / "Dockerfile.icecast").exists()

    def test_liquidsoap_dockerfile_exists(self):
        assert (LIQUIDSOAP_DIR / "Dockerfile").exists()

    def test_icecast_dockerfile_exposes_8000(self):
        content = (STREAMING_DIR / "Dockerfile.icecast").read_text()
        assert "EXPOSE 8000" in content

    def test_liquidsoap_dockerfile_copies_config(self):
        content = (LIQUIDSOAP_DIR / "Dockerfile").read_text()
        assert "channel.liq" in content
        assert "entrypoint.sh" in content
