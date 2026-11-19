import pytest
from src.validators import validate_ip, validate_list, expand_range, ValidationError


class TestValidateIP:
    def test_valid_ip(self):
        assert validate_ip("8.8.8.8") == "8.8.8.8"
    def test_normalizes_whitespace(self):
        assert validate_ip("  1.1.1.1  ") == "1.1.1.1"
    def test_invalid_octet(self):
        with pytest.raises(ValidationError):
            validate_ip("999.1.1.1")
    def test_invalid_format(self):
        with pytest.raises(ValidationError):
            validate_ip("not-an-ip")
    def test_empty(self):
        with pytest.raises(ValidationError):
            validate_ip("")


class TestValidateList:
    def test_multiple_valid(self):
        v, e = validate_list("8.8.8.8, 1.1.1.1")
        assert v == ["8.8.8.8", "1.1.1.1"]
        assert e == []
    def test_deduplicates(self):
        v, _ = validate_list("8.8.8.8, 8.8.8.8, 1.1.1.1")
        assert v == ["8.8.8.8", "1.1.1.1"]
    def test_mixed_valid_invalid(self):
        v, e = validate_list("8.8.8.8, 999.1.1.1")
        assert v == ["8.8.8.8"]
        assert len(e) == 1
    def test_empty_input(self):
        v, e = validate_list("")
        assert v == []
        assert e


class TestExpandRange:
    def test_single_ip(self):
        assert expand_range("192.168.1.1") == ["192.168.1.1"]
    def test_range_last_octet(self):
        assert expand_range("192.168.1.1-3") == ["192.168.1.1", "192.168.1.2", "192.168.1.3"]
    def test_cidr_slash_30(self):
        r = expand_range("192.168.1.0/30")
        assert "192.168.1.1" in r
        assert "192.168.1.2" in r
