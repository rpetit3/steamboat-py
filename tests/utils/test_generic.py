import sys

import pytest

from steamboat.utils.generic import (
    check_dependency,
    execute,
    get_platform,
    validate_file,
)


class TestValidateFile:
    def test_returns_absolute_path_string(self, tmp_path):
        f = tmp_path / "data.txt"
        f.write_text("content")
        result = validate_file(str(f))
        assert result == str(f.absolute())
        assert isinstance(result, str)

    def test_raises_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError, match="not found"):
            validate_file(str(tmp_path / "missing.txt"))

    def test_raises_value_error_for_empty_file(self, tmp_path):
        f = tmp_path / "empty.txt"
        f.write_text("")
        with pytest.raises(ValueError, match="is empty"):
            validate_file(str(f))


class TestGetPlatform:
    def test_returns_linux_or_mac(self):
        result = get_platform()
        assert result in ("linux", "mac")


class TestCheckDependency:
    def test_finds_known_program(self):
        result = check_dependency("python3")
        assert result is not None
        assert "python3" in result

    def test_exits_for_missing_program(self):
        with pytest.raises(SystemExit):
            check_dependency("definitely_not_a_real_program_xyz")


class TestExecute:
    def test_capture_simple_command(self):
        stdout, stderr = execute("echo hello", capture=True)
        assert stdout.strip() == "hello"

    def test_returns_true_without_capture(self):
        result = execute("true")
        assert result is True

    def test_allow_fail_returns_none(self):
        result = execute("false", allow_fail=True)
        assert result is None

    def test_failing_command_exits(self):
        with pytest.raises(SystemExit):
            execute("false", allow_fail=False)

    def test_piped_command(self):
        stdout, stderr = execute("echo hello | cat", capture=True)
        assert stdout.strip() == "hello"

    def test_capture_multiword_output(self):
        stdout, stderr = execute("echo one two three", capture=True)
        assert stdout.strip() == "one two three"
