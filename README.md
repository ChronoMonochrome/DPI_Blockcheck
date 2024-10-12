# DPI Block Check

A Python script to check the accessibility of various websites while using the [GoodbyeDPI](https://github.com/ValdikSS/GoodbyeDPI) or [zapret](https://github.com/bol-van/zapret) projects. The script tests the availability of websites by launching GoodbyeDPI / zapret, which are tools that helps bypass blocking restrictions.

## Prerequisites

Before running the script, ensure that:
- GoodbyeDPI/zapret service is not running on the system.
- Any VPNs or similar services are **disabled** to obtain accurate results.
- Note: the zapret service on Linux is restarted by this script automatically, so stopping it before running the script is not necessary

## Features

- Tests a predefined list of websites to determine if they are accessible
- Logs the results to a text file

## Inspiration

This script is inspired by another project found at [NTC Party](https://ntc.party/t/goodcheck-блокчек-скрипт-для-goodbyedpi-zapret-byedpi/10880/446).

## Installation

1. Clone this repository to your local machine:
   ```bash
   git clone https://github.com/ChronoMonochrome/dpi-block-check.git
   cd dpi-block-check
2. If cloning this repo first time, run `python download_files.py`. The required files will be downloaded to bin folder. For zapret to work on Windows, it's required that the cygwin is installed to C:/cygwin64 (or a file C:/cygwin64/bin/cygwin1.dll is present)
3. Run blockcheck.py (e.g. from cmd.exe) with admin privileges:
   `python blockcheck.py --tool=zapret`
or
   `python blockcheck.py --tool=goodbyedpi`
4. To test your current configuration without stopping the system service, enable GoodbyeDPI/zapret service and use --tool=none
