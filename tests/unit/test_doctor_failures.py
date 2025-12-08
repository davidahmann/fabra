from meridian.doctor import check_redis, check_postgres
from unittest.mock import patch


def test_doctor_redis_fail() -> None:
    with patch("redis.from_url", side_effect=Exception("Connection refused")):
        res = check_redis("redis://bad")
        assert res["status"] == "❌ Failed"
        assert "Connection refused" in res["details"]


def test_doctor_postgres_fail() -> None:
    with patch("sqlalchemy.create_engine", side_effect=Exception("Auth failed")):
        res = check_postgres("postgres://bad")
        assert res["status"] == "❌ Failed"
        assert "Auth failed" in res["details"]
