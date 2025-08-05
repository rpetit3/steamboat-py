import logging
import sys

from steamboat.io.table import read_table

NWSS_FIELDS = [
    "reporting_jurisdiction",
    "site_id",
    "county_names",
    "other_jurisdiction",
    "zipcode",
    "population_served",
    "sample_location",
    "sample_location_specify",
    "institution_type",
    "epaid",
    "wwtp_name",
    "wwtp_jurisdiction",
    "capacity_mgd",
    "sample_type",
    "sample_matrix",
    "pretreatment",
    "concentration_method",
    "extraction_method",
    "rec_eff_target_name",
    "rec_eff_spike_matrix",
    "rec_eff_spike_conc",
    "pasteurized",
    "pcr_target",
    "pcr_gene_target",
    "pcr_gene_target_ref",
    "pcr_type",
    "lod_ref",
    "quant_stan_type",
    "stan_ref",
    "inhibition_method",
    "num_no_target_control",
    "sample_collect_date",
    "sample_collect_time",
    "flow_rate",
    "collection_water_temp",
    "sample_id",
    "lab_id",
    "test_result_date",
    "pcr_target_units",
    "pcr_target_avg_conc",
    "lod_sewage",
    "ntc_amplify",
    "rec_eff_percent",
    "inhibition_detect",
    "inhibition_adjust",
    "major_lab_method",
    "major_lab_method_desc"
]

def _process_row(row: dict, mappings: dict) -> dict:
    """
    Process a row from the NWSS results file and return a dictionary of values

    Args:
        row (dict): A dictionary representing a row in the NWSS results file
        mappings (dict): A dictionary mapping field names to their NWSS equivalents and other constants

    Returns:
        dict: A dictionary of processed values

    Example Columns and Values
        WPHL ID#	230000001
        Site	City_Name
        PackageOK	Yes
        WastewaterTempF	66
        DailyTotalGallons	3.941
        SampleCollected	8/8/2023 7:00
        SampleProcessed	8/9/2023
        SiteDescription	Influent
        Comments	
        [BCoV]	47.43
        [SC2]	0.211
        [Flu A]	0
        [Flu B]	0
        [MeV]	
        [RSV]	
        [NoroGI]	
        [NoroGII]	
        Recovery Efficiency	43.93%
        Estimated SC2 orig conc	4119.27
        Estimated Flu A orig conc	0
        Estimated Flu B orig conc	0
        Estimated RSV orig conc	0
        Estimated NoroGI orig conc	0
        Estimated NoroGII orig conc	0
        Avg recovery eff	36.70%
        Avg est SC2 conc pre recovery cntrl	9466.67
        Avg est SC2 conc post recov cntrl	25791.49
        Avg est FluA conc pre recov cntrl	800
        Avg est FluA conc post recov cntrl	2179.56
        Avg est FluB conc pre recov cntrl	0
        Avg est FluB conc post recov cntrl	0
        Avg est MV conc pre recov cntrl	
        Avg est MV conc post recov cntrl	
        Avg est RSV conc pre recov cntrl	0
        Avg est RSV conc post recov cntrl	0
        Avg est NoroGI conc pre recov cntrl	0
        Avg est NoroGI conc post recov cntrl	0
        Avg est NoroGII conc pre recov cntrl	0
        Avg est NoroGII conc post recov cntrl	0

    Example remapping of columns:
    column_mappings:
        sample_id: "WPHL ID#"
        collection_water_temp: "WastewaterTempF"
        flow_rate: "DailyTotalGallons"
        sample_collect_date: "SampleCollected"
        test_result_date: "SampleProcessed"
        rec_eff_percent: "Avg recovery eff"
        # a list of tested targets and their corresponding columns
        targets:
            sars_cov_2: "Avg est SC2 conc pre recovery cntrl"
            influenza_a: "Avg est FluA conc pre recov cntrl"
            influenza_b: "Avg est FluB conc pre recov cntrl"
            rsv: "Avg est RSV conc pre recov cntrl"
            mv: "Avg est MV conc pre recov cntrl"
            noro_gi: "Avg est NoroGI conc pre recov cntrl"
            noro_gii: "Avg est NoroGII conc pre recov cntrl"

    The 'sample_collect_date' is split into two parts:
        - The date part is put in the "sample_collect_date" field
        - The time part is put in the "sample_collect_time" field

    The "targets" contains is split into two parts:
        - The target key (e.g., "sars_cov_2") is put in the "pcr_target" field
        - The target value of the mapped column is put in the "pcr_target_avg_conc"
    
    For "targets" columns, if the value is empty, produce a warning and do not log the value.
    """
    row_results = {}
    sample_id = row[mappings['column_mappings']['sample_id']]

    """
    Add shared fields to the row results that tend to be constant across samples.

    Example Mapping:
        # Occasionally update
        rec_eff_spike_conc: 0.0

        # Constant Columns
        inhibition_detect: ""
        inhibition_adjust: ""
        lab_id: ""
        lod_sewage: 0000
        major_lab_method: 0
        major_lab_method_desc: ""
        ntc_amplify: ""
        pasteurized: ""
        pcr_target_units: ""
    """
    shared_fields = {
        'sample_id': sample_id,
        
        # Taken from the YAML mappings
        "rec_eff_spike_conc": mappings['rec_eff_spike_conc'],
        'inhibition_detect': mappings['inhibition_detect'],
        'inhibition_adjust': mappings['inhibition_adjust'],
        'lab_id': mappings['lab_id'],
        'lod_sewage': mappings['lod_sewage'],
        'major_lab_method': mappings['major_lab_method'],
        'major_lab_method_desc': mappings['major_lab_method_desc'],
        'ntc_amplify': mappings['ntc_amplify'],
        'pasteurized': mappings['pasteurized'],
        'pcr_target_units': mappings['pcr_target_units'],
    }

    # Test if Temp is a digit
    if row[mappings['column_mappings']['collection_water_temp']].replace('.','',1).isdigit():
        shared_fields['collection_water_temp'] = f"{(float(row[mappings['column_mappings']['collection_water_temp']]) - 32) * 5 / 9:.2f}"  # Convert Fahrenheit to Celsius
    else:
        logging.warning(f"Collection water temperature ({row[mappings['column_mappings']['collection_water_temp']]}) for sample {sample_id} is not a number, skipping conversion and leaving empty")
        shared_fields['collection_water_temp'] = ""

    #  Check flow rate is a digit
    if row[mappings['column_mappings']['flow_rate']].replace('.','',1).isdigit():
        shared_fields['flow_rate'] = float(row[mappings['column_mappings']['flow_rate']])
    else:
        logging.warning(f"Flow rate ({row[mappings['column_mappings']['flow_rate']]}) for sample {sample_id} is not a number, leaving empty")
        shared_fields['flow_rate'] = ""

    """
    Add site related fields to the shared fields.

    Example Mapping
    sites:
        site_name:
            reporting_jurisdiction: ""
            site_id: ""
            county_names: 00000
            other_jurisdiction: ""
            zipcode: "00000"
            population_served: 00000
            sample_location: ""
            sample_location_specify: ""
            institution_type: ""
            epaid: ""
            wwtp_name: ""
            wwtp_jurisdiction: ""
            capacity_mgd: 0.0
            sample_type: ""
            sample_matrix: ""
            pretreatment: ""
            concentration_method: ""
            extraction_method: ""
            rec_eff_target_name: ""
            rec_eff_spike_matrix: ""
    """
    site_id = row[mappings['column_mappings']['site']].lower().replace(" ", "_")
    if site_id not in mappings['sites']:
        logging.warning(f"Site '{site_id}' not found in mappings, skipping sample {sample_id}")
        return {}
    shared_fields['reporting_jurisdiction'] = mappings['sites'][site_id]['reporting_jurisdiction']
    shared_fields['site_id'] = mappings['sites'][site_id]['site_id']
    shared_fields['county_names'] = mappings['sites'][site_id]['county_names']
    shared_fields['other_jurisdiction'] = mappings['sites'][site_id]['other_jurisdiction']
    shared_fields['zipcode'] = mappings['sites'][site_id]['zipcode']
    shared_fields['population_served'] = mappings['sites'][site_id]['population_served']
    shared_fields['sample_location'] = mappings['sites'][site_id]['sample_location']
    shared_fields['sample_location_specify'] = mappings['sites'][site_id]['sample_location_specify']
    shared_fields['institution_type'] = mappings['sites'][site_id]['institution_type']
    shared_fields['epaid'] = mappings['sites'][site_id]['epaid']
    shared_fields['wwtp_name'] = mappings['sites'][site_id]['wwtp_name']
    shared_fields['wwtp_jurisdiction'] = mappings['sites'][site_id]['wwtp_jurisdiction']
    shared_fields['capacity_mgd'] = mappings['sites'][site_id]['capacity_mgd']
    shared_fields['sample_type'] = mappings['sites'][site_id]['sample_type']
    shared_fields['sample_matrix'] = mappings['sites'][site_id]['sample_matrix']
    shared_fields['pretreatment'] = mappings['sites'][site_id]['pretreatment']
    shared_fields['concentration_method'] = mappings['sites'][site_id]['concentration_method']
    shared_fields['extraction_method'] = mappings['sites'][site_id]['extraction_method']
    shared_fields['rec_eff_target_name'] = mappings['sites'][site_id]['rec_eff_target_name']
    shared_fields['rec_eff_spike_matrix'] = mappings['sites'][site_id]['rec_eff_spike_matrix']

    # Add rec_eff_percent
    shared_fields['rec_eff_percent'] = row[mappings['column_mappings']['rec_eff_percent']].replace("%", "")

    row_results = []
    for target, nwss_mapping in mappings['column_mappings']['targets'].items():
        if nwss_mapping in row:
            value = row[nwss_mapping]
            if value == "":
                logging.warning(f"Value for '{target}' in sample {sample_id} is empty, skipping")
                continue
            else:
                if target not in mappings['targets']:
                    logging.warning(f"Target {target} not found in mappings, skipping")
                    continue
                else:
                    """
                    Add target specific fields to the row result.

                    Example Mapping:
                        targets:
                            - TARGET_ID:
                                pcr_target: ""
                                pcr_gene_target: ""
                                pcr_gene_target_ref: ""
                                pcr_type: ""
                                lod_ref: ""
                                quant_stan_type: ""
                                stan_ref: ""
                                inhibition_method: ""
                    """
                    # Combine the shared fields with the row result
                    row_results.append({
                        **shared_fields,
                        'pcr_target_avg_conc': value,
                        'pcr_target': mappings['targets'][target]['pcr_target'],
                        'pcr_gene_target': mappings['targets'][target]['pcr_gene_target'],
                        'pcr_gene_target_ref': mappings['targets'][target]['pcr_gene_target_ref'],
                        'pcr_type': mappings['targets'][target]['pcr_type'],
                        'lod_ref': mappings['targets'][target]['lod_ref'],
                        'quant_stan_type': mappings['targets'][target]['quant_stan_type'],
                        'stan_ref': mappings['targets'][target]['stan_ref'],
                        'inhibition_method': mappings['targets'][target]['inhibition_method'],
                        'sample_collect_date': row[mappings['column_mappings']['sample_collect_date']].split()[0],
                        'sample_collect_time': row[mappings['column_mappings']['sample_collect_date']].split()[1],
                        'test_result_date': row[mappings['column_mappings']['test_result_date']],
                    })
        else:
            logging.warning(f"Target {target} not found in row for sample {sample_id}, skipping")

    return row_results

def parse_results(input: str, mappings: dict) -> dict:
    """
    Parse a results file and return a dictionary of results

    Args:
        input (str): input results file to be parsed in TSV or CSV format
        mappings (dict): A dictionary containing the mappings for the fields and targets

    Returns:
        dict: A dictionary of results

    Examples:
        >>> from steamboat.repos.nwss import parse_results
        >>> results = parse_results("data.tsv", mappings)
    """
    logging.debug(f"Parsing results from {input}")
    results = []
    for row in read_table(input):
        row_results = _process_row(row, mappings)
        results.extend(row_results)

    return results
