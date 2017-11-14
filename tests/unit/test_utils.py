from conu.utils.core import random_str


def test_random_str():
    assert random_str()
    assert random_str() != random_str()
    assert len(random_str(size=42)) == 42
    assert len(random_str(2)) == 2
