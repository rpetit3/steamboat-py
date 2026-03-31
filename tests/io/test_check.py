import pytest

from steamboat.io.check import check_file, file_exists_error


class TestCheckFile:
    def test_returns_absolute_path(self, tmp_path):
        f = tmp_path / "data.txt"
        f.write_text("content")
        result = check_file(str(f))
        assert result == f.absolute()

    def test_raises_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError, match="not found"):
            check_file(str(tmp_path / "missing.txt"))

    def test_raises_value_error_for_empty_file(self, tmp_path):
        f = tmp_path / "empty.txt"
        f.write_text("")
        with pytest.raises(ValueError, match="is empty"):
            check_file(str(f))


class TestFileExistsError:
    def test_raises_when_file_exists_no_force(self, tmp_path):
        f = tmp_path / "output.csv"
        f.write_text("data")
        with pytest.raises(FileExistsError, match="already exists"):
            file_exists_error(str(f), force=False)

    def test_no_error_when_file_exists_with_force(self, tmp_path):
        f = tmp_path / "output.csv"
        f.write_text("data")
        file_exists_error(str(f), force=True)

    def test_no_error_when_file_missing(self, tmp_path):
        file_exists_error(str(tmp_path / "nonexistent.csv"), force=False)
