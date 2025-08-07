import os
import pytest
from personal_chatbot.src import file_handler as fh


def test_safe_join_blocks_absolute_and_traversal(tmp_path):
    base = tmp_path

    # Absolute path outside base should be rejected
    outside = os.path.abspath(os.path.join(os.path.sep, "etc", "passwd"))
    with pytest.raises(ValueError):
        fh.safe_join(base, outside)

    # Relative traversal should be rejected
    with pytest.raises(ValueError):
        fh.safe_join(base, "../secrets.txt")

    # Nested traversal within segments should also be rejected
    with pytest.raises(ValueError):
        fh.safe_join(base, "nested/../../escape.txt")

    # Valid relative path within base succeeds
    p = fh.safe_join(base, "nested/file.txt")
    assert str(p).startswith(str(base))
    assert p.parent.name == "nested"