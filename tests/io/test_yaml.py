from steamboat.io.yaml import read_yaml, write_yaml


class TestReadYaml:
    def test_read_dict(self, tmp_path):
        f = tmp_path / "data.yaml"
        f.write_text("key1: value1\nkey2: value2\n")
        result = read_yaml(str(f))
        assert result == {"key1": "value1", "key2": "value2"}

    def test_read_list(self, tmp_path):
        f = tmp_path / "data.yaml"
        f.write_text("- alpha\n- beta\n- gamma\n")
        result = read_yaml(str(f))
        assert result == ["alpha", "beta", "gamma"]

    def test_read_nested(self, tmp_path):
        f = tmp_path / "data.yaml"
        f.write_text("parent:\n  child: value\n")
        result = read_yaml(str(f))
        assert result == {"parent": {"child": "value"}}


class TestWriteYaml:
    def test_write_dict(self, tmp_path):
        f = tmp_path / "out.yaml"
        write_yaml(str(f), {"key": "value"})
        content = f.read_text()
        assert "key: value" in content

    def test_write_list(self, tmp_path):
        f = tmp_path / "out.yaml"
        write_yaml(str(f), ["a", "b", "c"])
        content = f.read_text()
        assert "- a" in content
        assert "- b" in content


class TestYamlRoundtrip:
    def test_dict_roundtrip(self, tmp_path):
        f = tmp_path / "roundtrip.yaml"
        original = {"sites": {"site_a": {"id": 1}, "site_b": {"id": 2}}}
        write_yaml(str(f), original)
        result = read_yaml(str(f))
        assert result == original

    def test_list_roundtrip(self, tmp_path):
        f = tmp_path / "roundtrip.yaml"
        original = ["alpha", "beta", "gamma"]
        write_yaml(str(f), original)
        result = read_yaml(str(f))
        assert result == original
