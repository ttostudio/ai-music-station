from __future__ import annotations

from pathlib import Path

import pytest
import yaml

COMPOSE_FILE = Path(__file__).parent.parent / "docker-compose.yml"


@pytest.fixture
def compose():
    return yaml.safe_load(COMPOSE_FILE.read_text())


class TestDockerCompose:
    def test_file_exists(self):
        assert COMPOSE_FILE.exists()

    def test_project_name(self, compose):
        assert compose.get("name") == "product-ai-music-station"

    def test_required_services_exist(self, compose):
        services = compose.get("services", {})
        required = [
            "postgres", "migrate", "api", "icecast",
            "liquidsoap",
            "frontend", "caddy",
        ]
        for svc in required:
            assert svc in services, f"Missing service: {svc}"

    def test_no_per_channel_liquidsoap(self, compose):
        """チャンネル別Liquidsoapサービスが存在しないことを確認"""
        services = compose.get("services", {})
        for name in services:
            assert not name.startswith("liquidsoap-"), (
                f"チャンネル別サービス '{name}' が残っています。"
                "統合 liquidsoap サービスを使用してください。"
            )

    def test_all_services_have_healthchecks(self, compose):
        services = compose.get("services", {})
        # migrate is run-once, doesn't need healthcheck
        skip = {"migrate"}
        for name, svc in services.items():
            if name in skip:
                continue
            assert "healthcheck" in svc, (
                f"Service '{name}' missing healthcheck"
            )

    def test_postgres_uses_volume(self, compose):
        pg = compose["services"]["postgres"]
        volumes = pg.get("volumes", [])
        assert any("pgdata" in str(v) for v in volumes)

    def test_caddy_exposes_3200(self, compose):
        caddy = compose["services"]["caddy"]
        ports = caddy.get("ports", [])
        assert any("3200" in str(p) for p in ports)

    def test_no_hardcoded_passwords(self, compose):
        content = COMPOSE_FILE.read_text()
        # Check no literal passwords (allow ${} and :? syntax)
        assert "password: changeme" not in content.lower()
        assert "password=changeme" not in content.lower()

    def test_migrate_runs_once(self, compose):
        migrate = compose["services"]["migrate"]
        assert migrate.get("restart") == "no"

    def test_liquidsoap_has_track_volume(self, compose):
        """統合liquidsoapサービスがtracksボリュームを持つことを確認"""
        svc = compose["services"]["liquidsoap"]
        volumes = svc.get("volumes", [])
        assert any("generated_tracks" in str(v) for v in volumes), (
            "liquidsoap missing tracks volume"
        )

    def test_liquidsoap_depends_on_api(self, compose):
        """liquidsoapがAPIに依存していることを確認（チャンネル一覧取得のため）"""
        svc = compose["services"]["liquidsoap"]
        depends = svc.get("depends_on", {})
        assert "api" in depends, (
            "liquidsoap must depend on api for channel discovery"
        )

    def test_liquidsoap_has_api_base_url(self, compose):
        """liquidsoapにAPI_BASE_URL環境変数が設定されていることを確認"""
        svc = compose["services"]["liquidsoap"]
        env = svc.get("environment", {})
        assert "API_BASE_URL" in env, (
            "liquidsoap missing API_BASE_URL environment variable"
        )


class TestEnvExample:
    def test_env_example_exists(self):
        env_file = Path(__file__).parent.parent / ".env.example"
        assert env_file.exists()

    def test_required_vars_present(self):
        env_file = Path(__file__).parent.parent / ".env.example"
        content = env_file.read_text()
        required_vars = [
            "DB_PASSWORD",
            "ICECAST_SOURCE_PASSWORD",
            "ICECAST_ADMIN_PASSWORD",
            "FRONTEND_PORT",
        ]
        for var in required_vars:
            assert var in content, f"Missing env var: {var}"


class TestCaddyfile:
    def test_caddyfile_exists(self):
        caddyfile = Path(__file__).parent.parent / "caddy" / "Caddyfile"
        assert caddyfile.exists()

    def test_routes_api(self):
        content = (
            Path(__file__).parent.parent / "caddy" / "Caddyfile"
        ).read_text()
        assert "/api/*" in content
        assert "api:8000" in content

    def test_routes_stream(self):
        content = (
            Path(__file__).parent.parent / "caddy" / "Caddyfile"
        ).read_text()
        assert "/stream/*" in content
        assert "icecast:8000" in content

    def test_routes_frontend(self):
        content = (
            Path(__file__).parent.parent / "caddy" / "Caddyfile"
        ).read_text()
        assert "frontend:80" in content

    def test_blocks_internal(self):
        content = (
            Path(__file__).parent.parent / "caddy" / "Caddyfile"
        ).read_text()
        assert "/internal/*" in content
        assert "404" in content
