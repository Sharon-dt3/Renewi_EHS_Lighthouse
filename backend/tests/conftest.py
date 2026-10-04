import pytest

from backend import security as sec


@pytest.fixture(autouse=True)
def _cheap_scrypt(monkeypatch):
    """Tests create many accounts; use a tiny scrypt cost so the suite stays fast. Production keeps 2**14."""
    monkeypatch.setattr(sec, "SCRYPT_COST", (16, 8, 1))
