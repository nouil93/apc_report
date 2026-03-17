# APC Report Tool

A professional Python CLI tool for collecting telemetry from APC UPS web interfaces and generating automated monitoring reports.

The tool authenticates against APC Network Management Card (NMC) web pages, extracts historical environmental and power telemetry, normalizes the data into pandas DataFrames, and exports both plots and PDF reports.

## Why this project exists

APC UPS appliances often expose useful operational data through a web UI, but extracting that information consistently for reporting, trending, and capacity review is tedious. This tool automates that workflow and turns appliance telemetry into reusable data and readable reports.

## Features

- Collect telemetry from one or more APC devices
- Authenticate with APC NMC web interfaces
- Parse historical log pages into structured datasets
- Compute daily min/max values for key temperature metrics
- Generate SVG charts with Plotly
- Build PDF reports with summary tables
- Export CSV datasets for further analysis
- Configurable TLS verification per device
- Clean CLI with focused subcommands

## Architecture

```text
APC NMC Web UI
      │
      ▼
HTTP session + login
      │
      ▼
HTML scraping (BeautifulSoup)
      │
      ▼
Normalization (pandas DataFrame)
      │
      ├── Daily min/max summary
      ├── CSV export
      ├── Plotly SVG chart
      ▼
PDF report generation
```

## Repository layout

```text
apc-report-tool/
├── LICENSE
├── README.md
├── pyproject.toml
├── requirements.txt
├── config.example.yaml
├── examples/
│   └── sample_report_workflow.md
├── src/
│   └── apc_report/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py
│       ├── config.py
│       ├── constants.py
│       ├── models.py
│       ├── scraper.py
│       ├── reporting.py
│       └── utils.py
└── tests/
    ├── test_config.py
    └── test_utils.py
```

## Installation

### Local development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

## Configuration

Create a YAML file from the example template:

```bash
cp config.example.yaml config.yaml
```

Example structure:

```yaml
output_dir: ./reports
verify_tls_default: true

devices:
  - name: apc_rack_a
    url: https://apc-rack-a.example.local
    username: apcuser
    password: change-me
    verify_tls: false
  - name: apc_rack_b
    url: https://apc-rack-b.example.local
    username: apcuser
    password: change-me
```

## Usage

Generate reports for every configured device:

```bash
apc-report report --config ./config.yaml
```

Export a CSV for a single device:

```bash
apc-report collect --config ./config.yaml --device apc_rack_a --csv
```

Write output to a custom directory:

```bash
apc-report report --config ./config.yaml --output-dir ./artifacts
```

## Security notes

- Do not commit real credentials or internal URLs.
- Prefer valid TLS certificates whenever possible.
- Use `verify_tls: false` only for trusted internal appliances that cannot be upgraded.
- Review generated reports before sharing externally.

## Operational notes

This project targets APC web interfaces that expose historical log pages through the NMC HTML UI. Page structure varies between appliance firmware versions, so minor selector adjustments may be needed for your environment.

## Roadmap

- Add JSON export
- Add richer charts for battery and load metrics
- Add unit tests for HTML parsing fixtures
- Add optional Prometheus export mode
- Add packaging for internal PyPI distribution

## License

This project is licensed under the GNU General Public License v3.0 (GPL-3.0).

Copyright (C) 2026 Frederic Delacour
