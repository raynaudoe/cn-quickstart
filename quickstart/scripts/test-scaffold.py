#!/usr/bin/env python3
"""Regression tests for bootstrap failures and Make configuration validation."""

import os
from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parent.parent
BOOTSTRAP = ROOT / "docker/modules/splice-onboarding/docker/utils.sh"
BOOTSTRAP_HARNESS = r'''
source "$1"
curl() {
  case "$*" in
    *http://participant/v2/users/backend-user*)
      printf '{}\n%s\n' "$PROBE_STATUS"
      ;;
    *http://participant/v2/users*)
      echo CREATION_REQUEST >&2
      printf '{"user":{"id":"backend-user"}}\n%s\n' "$CREATE_STATUS"
      ;;
    *) return 7 ;;
  esac
}
create_user test-token backend-user backend-name '' participant
'''


class BootstrapTests(unittest.TestCase):
    def run_bootstrap(self, probe_status, create_status=201):
        return subprocess.run(
            ["bash", "-c", BOOTSTRAP_HARNESS, "bootstrap-test", str(BOOTSTRAP)],
            env={**os.environ, "PROBE_STATUS": str(probe_status), "CREATE_STATUS": str(create_status)},
            text=True, capture_output=True,
        )

    def test_existing_user_does_not_trigger_creation(self):
        result = self.run_bootstrap(200)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("CREATION_REQUEST", result.stderr)

    def test_absent_user_is_created(self):
        result = self.run_bootstrap(404)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "backend-user")
        self.assertIn("CREATION_REQUEST", result.stderr)

    def test_failed_lookup_stops_provisioning(self):
        for status in (401, 403, 500, 503, 0):
            with self.subTest(status=status):
                result = self.run_bootstrap(status)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(f"HTTP {status}", result.stderr)
                self.assertNotIn("CREATION_REQUEST", result.stderr)

    def test_failed_creation_is_not_reported_as_success(self):
        result = self.run_bootstrap(404, 500)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("CREATION_REQUEST", result.stderr)


class ConfigurationTests(unittest.TestCase):
    def test_supported_configurations_are_accepted(self):
        for mode in ("shared-secret", "oauth2"):
            for pqs in ("false", "true"):
                with self.subTest(mode=mode, pqs=pqs):
                    result = subprocess.run(
                        ["make", "--no-print-directory", "help", f"AUTH_MODE={mode}", f"PQS_ENABLED={pqs}"],
                        cwd=ROOT, text=True, capture_output=True,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)

    def test_empty_combined_and_unknown_values_are_rejected(self):
        for setting, combined in (("AUTH_MODE", "shared-secret oauth2"), ("PQS_ENABLED", "true false")):
            for value in ("", combined, "unknown"):
                with self.subTest(setting=setting, value=value):
                    result = subprocess.run(
                        ["make", "--no-print-directory", "help", "AUTH_MODE=oauth2", "PQS_ENABLED=false",
                         f"{setting}={value}"],
                        cwd=ROOT, text=True, capture_output=True,
                    )
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(f"{setting} must be", result.stderr)


if __name__ == "__main__":
    unittest.main()
