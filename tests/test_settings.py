from __future__ import annotations

import pytest
from pydantic import ValidationError

from config.settings import Settings


def test_settings_accept_required_core_base_url() -> None:
    settings = Settings(
        _env_file=None,
        CORE_BASE_URL="http://127.0.0.1:3100",
        TEMPORAL_TASK_QUEUE="phantom-strike-signal-validation",
    )

    assert settings.core_base_url == "http://127.0.0.1:3100"
    assert settings.temporal_task_queue == "phantom-strike-signal-validation"


def test_settings_require_core_base_url() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None)
