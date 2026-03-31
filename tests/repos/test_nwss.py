from steamboat.repos.nwss import _process_row

# Minimal mappings fixture matching the structure expected by _process_row
MAPPINGS = {
    "column_mappings": {
        "sample_id": "WPHL ID#",
        "collection_water_temp": "WastewaterTempF",
        "flow_rate": "DailyTotalGallons",
        "sample_collect_date": "SampleCollected",
        "test_result_date": "SampleProcessed",
        "rec_eff_percent": "Avg recovery eff",
        "site": "Site",
        "targets": {
            "sars_cov_2": "Avg est SC2 conc",
        },
    },
    "sites": {
        "test_city": {
            "reporting_jurisdiction": "WY",
            "site_id": "SITE001",
            "county_names": "Test County",
            "other_jurisdiction": "",
            "zipcode": "82001",
            "population_served": 50000,
            "sample_location": "influent",
            "sample_location_specify": "",
            "institution_type": "",
            "epaid": "WY0000001",
            "wwtp_name": "Test WWTP",
            "wwtp_jurisdiction": "WY",
            "capacity_mgd": 5.0,
            "sample_type": "composite",
            "sample_matrix": "raw wastewater",
            "pretreatment": "none",
            "concentration_method": "PEG",
            "extraction_method": "QIAamp",
            "rec_eff_target_name": "BCoV",
            "rec_eff_spike_matrix": "pre-extraction",
        },
    },
    "targets": {
        "sars_cov_2": {
            "pcr_target": "sars-cov-2",
            "pcr_gene_target": "N gene",
            "pcr_gene_target_ref": "CDC N1",
            "pcr_type": "dPCR",
            "lod_ref": "REF001",
            "quant_stan_type": "plasmid",
            "stan_ref": "STAN001",
            "inhibition_method": "dilution",
        },
    },
    "rec_eff_spike_conc": 0.0,
    "inhibition_detect": "",
    "inhibition_adjust": "",
    "lab_id": "LAB001",
    "lod_sewage": 1000,
    "major_lab_method": 0,
    "major_lab_method_desc": "",
    "ntc_amplify": "",
    "pasteurized": "",
    "pcr_target_units": "copies/L",
}


def _make_row(**overrides):
    """Build a default valid NWSS input row, with optional overrides."""
    row = {
        "WPHL ID#": "230000001",
        "Site": "Test City",
        "WastewaterTempF": "66",
        "DailyTotalGallons": "3.941",
        "SampleCollected": "8/8/2023 7:00",
        "SampleProcessed": "8/9/2023",
        "Avg recovery eff": "43.93%",
        "Avg est SC2 conc": "9466.67",
    }
    row.update(overrides)
    return row


class TestProcessRow:
    def test_valid_row_returns_results(self):
        results = _process_row(_make_row(), MAPPINGS)
        assert len(results) == 1
        r = results[0]
        assert r["sample_id"] == "230000001"
        assert r["pcr_target"] == "sars-cov-2"
        assert r["pcr_target_avg_conc"] == "9466.67"
        assert r["site_id"] == "SITE001"
        assert r["reporting_jurisdiction"] == "WY"
        assert r["pcr_target_units"] == "copies/L"

    def test_temperature_conversion(self):
        results = _process_row(_make_row(), MAPPINGS)
        temp_c = float(results[0]["collection_water_temp"])
        # 66F = (66-32)*5/9 = 18.89C
        assert abs(temp_c - 18.89) < 0.01

    def test_non_numeric_temperature(self):
        results = _process_row(_make_row(WastewaterTempF="N/A"), MAPPINGS)
        assert results[0]["collection_water_temp"] == ""

    def test_non_numeric_flow_rate(self):
        results = _process_row(_make_row(DailyTotalGallons="unknown"), MAPPINGS)
        assert results[0]["flow_rate"] == ""

    def test_numeric_flow_rate(self):
        results = _process_row(_make_row(DailyTotalGallons="5.5"), MAPPINGS)
        assert results[0]["flow_rate"] == 5.5

    def test_unknown_site_returns_empty(self):
        row = _make_row(Site="Nonexistent City")
        results = _process_row(row, MAPPINGS)
        assert results == {}

    def test_exclusion_site_returns_empty(self):
        row = _make_row(Site="pt_something")
        results = _process_row(row, MAPPINGS)
        assert results == {}

    def test_exclude_prefix_returns_empty(self):
        row = _make_row(Site="exclude_site")
        results = _process_row(row, MAPPINGS)
        assert results == {}

    def test_empty_target_value_skipped(self):
        row = _make_row(**{"Avg est SC2 conc": ""})
        results = _process_row(row, MAPPINGS)
        assert results == []

    def test_rec_eff_percent_strips_percent(self):
        results = _process_row(_make_row(), MAPPINGS)
        assert results[0]["rec_eff_percent"] == "43.93"

    def test_sample_collect_date_split(self):
        results = _process_row(_make_row(), MAPPINGS)
        assert results[0]["sample_collect_date"] == "8/8/2023"
        assert results[0]["sample_collect_time"] == "7:00"
