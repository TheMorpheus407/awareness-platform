"""Minimal test to ensure pytest works and CI/CD can proceed."""

def test_basic_assertion():
    """Test that basic assertions work."""
    assert True
    assert 1 + 1 == 2
    assert "hello".upper() == "HELLO"


def test_basic_math():
    """Test basic mathematical operations."""
    assert 2 * 3 == 6
    assert 10 / 2 == 5
    assert 4 ** 2 == 16


def test_basic_string_operations():
    """Test basic string operations."""
    text = "pytest"
    assert len(text) == 6
    assert text.startswith("py")
    assert text.endswith("test")
    assert "test" in text


def test_basic_list_operations():
    """Test basic list operations."""
    items = [1, 2, 3, 4, 5]
    assert len(items) == 5
    assert sum(items) == 15
    assert max(items) == 5
    assert min(items) == 1


def test_basic_dict_operations():
    """Test basic dictionary operations."""
    data = {"name": "test", "value": 42}
    assert "name" in data
    assert data["value"] == 42
    assert len(data) == 2
    assert data.get("missing", "default") == "default"