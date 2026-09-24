#!/usr/bin/env python3
"""Validate local infrastructure configurations without starting containers."""

import json
from pathlib import Path
import subprocess


root = Path(__file__).resolve().parent.parent

for script in (root / "docker").rglob("*.sh"):
    subprocess.run(["bash", "-n", str(script)], check=True)

for mode in ("shared-secret", "oauth2"):
    for pqs in ("false", "true"):
        result = subprocess.run(
            ["make", "--no-print-directory", "compose-config", f"AUTH_MODE={mode}",
             f"PQS_ENABLED={pqs}", "CONFIG_ARGS=--format json"],
            cwd=root, text=True, capture_output=True, check=True,
        )
        if result.stderr.strip():
            raise RuntimeError(result.stderr)
        config = json.loads(result.stdout)
        services = config["services"]
        backend = services["backend-service"]
        env = backend["environment"]
        assert "build" in backend, "Backend must build inside Docker"
        assert not backend.get("ports"), "The API is exposed through the frontend proxy"
        assert services["frontend"]["depends_on"]["backend-service"]["condition"] == "service_healthy"
        for name in ("BACKEND_PORT", "POSTGRES_HOST", "POSTGRES_PORT", "POSTGRES_USERNAME", "POSTGRES_PASSWORD"):
            assert env[name], f"Missing backend configuration: {name}"
        assert env["POSTGRES_DATABASE"] == services["postgres"]["environment"]["CREATE_DATABASE_application"]
        assert not any(name.startswith("pqs") for name in backend["depends_on"])
        assert ("keycloak" in services) == (mode == "oauth2")
        assert ("pqs-app-provider" in services) == (pqs == "true")
        for name, service in services.items():
            if "build" in service:
                build = service["build"]
                context = Path(build["context"])
                assert context.is_dir(), f"Missing build context for {name}: {context}"
                assert (context / build.get("dockerfile", "Dockerfile")).is_file()
            for mount in service.get("volumes", []):
                if mount["type"] == "bind":
                    path = Path(mount["source"])
                    assert path.exists(), f"Missing bind mount for {name}: {path}"
        print(f"OK: {mode}, PQS={pqs}, {len(services)} services")

print("Shell syntax and Compose wiring checks passed.")
