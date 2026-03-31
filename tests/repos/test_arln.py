from steamboat.repos.arln import _process_gigatyper, _process_metadata


class TestProcessMetadata:
    def test_cre_sample_all_fields(self):
        row = {
            "Sample Type": "CRE",
            "LIMS ID #": "2401234",
            "SRR ID": "SRR12345678",
            "Extraction Date": "01/15/2024",
            "Date Sequenced": "01/20/2024",
        }
        result = _process_metadata(row)
        assert result["record_id"] == "2401234"
        assert result["arln_specimen_id"] == "2401234"
        assert result["wgs_id"] == "2024LC_2401234"
        assert result["srr_number"] == "SRR12345678"
        assert result["wgs_date_id_created"] == "01/15/2024"
        assert result["wgs_date_sent_to_seqfac"] == "01/15/2024"
        assert result["wgs_date_put_on_sequencer"] == "01/20/2024"

    def test_non_cre_sample_returns_empty(self):
        row = {
            "Sample Type": "OTHER",
            "LIMS ID #": "2401234",
            "SRR ID": "SRR12345678",
            "Extraction Date": "01/15/2024",
            "Date Sequenced": "01/20/2024",
        }
        result = _process_metadata(row)
        assert result == {}

    def test_cre_missing_fields_returns_missing(self):
        row = {
            "Sample Type": "CRE",
            "LIMS ID #": "2401234",
            "SRR ID": "",
            "Extraction Date": "01/15/2024",
            "Date Sequenced": "",
        }
        result = _process_metadata(row)
        assert "_missing" in result
        assert "SRR ID" in result["_missing"]
        assert "Date Sequenced" in result["_missing"]
        assert result["_sample"] == "2401234"

    def test_year_extraction_from_lims_id(self):
        row = {
            "Sample Type": "CRE",
            "LIMS ID #": "2599999",
            "SRR ID": "SRR00000001",
            "Extraction Date": "06/01/2025",
            "Date Sequenced": "06/05/2025",
        }
        result = _process_metadata(row)
        assert result["wgs_id"] == "2025LC_2599999"


class TestProcessGigatyper:
    def test_returns_sample_and_report(self):
        row = {"sample": "SAMPLE01", "formatted_report": "ST-123; KPC-2"}
        sample_id, report = _process_gigatyper(row)
        assert sample_id == "SAMPLE01"
        assert report == "ST-123; KPC-2"
