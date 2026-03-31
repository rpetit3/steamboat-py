import pytest

from steamboat.io.fasta import read_fasta, write_fasta

SAMPLE_FASTA = ">seq1\nATGCATGC\n>seq2\nGGGGAAAA\n"


class TestReadFasta:
    def test_read_as_dict(self, tmp_path):
        f = tmp_path / "seqs.fasta"
        f.write_text(SAMPLE_FASTA)
        result = read_fasta(str(f), "dict")
        assert result == {"seq1": "ATGCATGC", "seq2": "GGGGAAAA"}

    def test_read_as_list(self, tmp_path):
        f = tmp_path / "seqs.fasta"
        f.write_text(SAMPLE_FASTA)
        result = read_fasta(str(f), "list")
        assert result == ["ATGCATGC", "GGGGAAAA"]

    def test_invalid_return_type(self, tmp_path):
        f = tmp_path / "seqs.fasta"
        f.write_text(SAMPLE_FASTA)
        with pytest.raises(ValueError, match="Invalid return type"):
            read_fasta(str(f), "tuple")


class TestWriteFasta:
    def test_write_dict(self, tmp_path):
        f = tmp_path / "out.fasta"
        seqs = {"seq1": "ATGC", "seq2": "GGGG"}
        write_fasta(str(f), seqs)
        content = f.read_text()
        assert ">seq1\nATGC\n" in content
        assert ">seq2\nGGGG\n" in content

    def test_write_list(self, tmp_path):
        f = tmp_path / "out.fasta"
        seqs = ["ATGC", "GGGG"]
        write_fasta(str(f), seqs)
        content = f.read_text()
        assert ">seq0\nATGC\n" in content
        assert ">seq1\nGGGG\n" in content

    def test_invalid_type_raises(self, tmp_path):
        f = tmp_path / "out.fasta"
        with pytest.raises(ValueError, match="Invalid sequence type"):
            write_fasta(str(f), "not_a_dict_or_list")


class TestFastaRoundtrip:
    def test_dict_roundtrip(self, tmp_path):
        f = tmp_path / "roundtrip.fasta"
        original = {"contig1": "ATGCATGC", "contig2": "TTTTAAAA"}
        write_fasta(str(f), original)
        result = read_fasta(str(f), "dict")
        assert result == original

    def test_list_roundtrip(self, tmp_path):
        f = tmp_path / "roundtrip.fasta"
        original = ["ATGCATGC", "TTTTAAAA"]
        write_fasta(str(f), original)
        result = read_fasta(str(f), "list")
        assert result == original
