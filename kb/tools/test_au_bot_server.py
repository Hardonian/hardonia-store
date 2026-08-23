import os
import subprocess
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent


def test_au_bot_port_is_configurable_and_defaults_away_from_platform_port():
    env = os.environ.copy()
    env["AU_BOT_PORT"] = "8071"
    result = subprocess.run(
        [sys.executable, "-c", "import au_bot_server; print(au_bot_server.PORT)"],
        cwd=TOOLS,
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )
    assert result.stdout.strip() == "8071"
