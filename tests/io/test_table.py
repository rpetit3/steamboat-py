from steamboat.io.table import read_table, write_table


class TestReadTable:
    def test_tsv_with_header(self, tmp_path):
        f = tmp_path / "data.tsv"
        f.write_text("name\tvalue\nalpha\t1\nbeta\t2\n")
        result = read_table(str(f))
        assert result == [{"name": "alpha", "value": "1"}, {"name": "beta", "value": "2"}]

    def test_csv_with_header(self, tmp_path):
        f = tmp_path / "data.csv"
        f.write_text("name,value\nalpha,1\nbeta,2\n")
        result = read_table(str(f), delimiter=",")
        assert result == [{"name": "alpha", "value": "1"}, {"name": "beta", "value": "2"}]

    def test_tsv_without_header(self, tmp_path):
        f = tmp_path / "data.tsv"
        f.write_text("alpha\t1\nbeta\t2\n")
        result = read_table(str(f), has_header=False)
        assert result == [["alpha", "1"], ["beta", "2"]]


class TestWriteTable:
    def test_write_tsv(self, tmp_path):
        f = tmp_path / "out.tsv"
        data = [{"name": "alpha", "value": "1"}, {"name": "beta", "value": "2"}]
        write_table(str(f), data)
        content = f.read_text()
        assert "name\tvalue" in content
        assert "alpha\t1" in content
        assert "beta\t2" in content

    def test_write_csv(self, tmp_path):
        f = tmp_path / "out.csv"
        data = [{"name": "alpha", "value": "1"}, {"name": "beta", "value": "2"}]
        write_table(str(f), data, delimiter=",")
        content = f.read_text()
        assert "name,value" in content
        assert "alpha,1" in content

    def test_write_empty_values(self, tmp_path):
        f = tmp_path / "out.tsv"
        data = [{"name": "", "value": ""}]
        write_table(str(f), data)
        content = f.read_text()
        assert "name\tvalue" in content
        lines = content.strip().split("\n")
        assert len(lines) == 1  # header only


class TestTableRoundtrip:
    def test_roundtrip(self, tmp_path):
        f = tmp_path / "roundtrip.tsv"
        original = [{"col1": "a", "col2": "b"}, {"col1": "c", "col2": "d"}]
        write_table(str(f), original)
        result = read_table(str(f))
        assert result == original
