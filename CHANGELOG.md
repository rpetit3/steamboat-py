# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## v1.3.1

- Adjusted `arln-batch` to allow missing data without exiting (missing fields will be logged)
- Changed the parsing of wgs_id in `arln-batch`

## v1.3.0

### Added

- `ont-merge` command to merge ONT FASTQs from a run
- tests using pytest

## v1.2.0

### Added

- `arln-batch` command to batch metadata and GigaTyper results for ARLN submissions

## v1.1.1

### Added

- adjusted `nwss-batch` verbosity

## v1.1.0

### Added

- `nwws-batch` command to batch metadata and bioinformatics results for NWSS submissions

## v1.0.0

### Added

- Initial release
- `gisaid-batch` command to batch metadata and bioinformatics results for GISAID submissions
