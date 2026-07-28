import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.tools import USER_PROFILE_STORE, UserProfile, get_user_profile, update_user_profile


def test_user_profile_dataclass_round_trip():
    profile = UserProfile(user_id="u1", interests=["AI"], skills=["Python"])

    assert profile.user_id == "u1"
    assert profile.interests == ["AI"]
    assert profile.to_dict()["skills"] == ["Python"]


def test_update_user_profile_uses_structured_model():
    USER_PROFILE_STORE.clear()

    update_user_profile("u2", {"interests": ["AI"], "skills": ["Python"]})
    payload = json.loads(get_user_profile("u2"))

    assert payload["user_id"] == "u2"
    assert payload["interests"] == ["AI"]
    assert payload["skills"] == ["Python"]
    assert isinstance(USER_PROFILE_STORE["u2"], UserProfile)
