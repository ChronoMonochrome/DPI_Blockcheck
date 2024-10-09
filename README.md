
# GDPI Block Check

A Python script to check the accessibility of various websites while using the [GoodbyeDPI](https://github.com/ValdikSS/GoodbyeDPI) project. The script tests the availability of websites by launching GoodbyeDPI, which is a tool that helps bypass blocking restrictions.

## Prerequisites

Before running the script, ensure that:
- GoodbyeDPI service is not running on the system.
- Any VPNs or similar services are **disabled** to obtain accurate results. 

## Features

- Tests a predefined list of websites to determine if they are accessible
- Logs the results to a text file

## Inspiration

This script is inspired by another project found at [NTC Party](https://ntc.party/t/goodcheck-блокчек-скрипт-для-goodbyedpi-zapret-byedpi/10880/446).

## Installation

1. Clone this repository to your local machine:
   ```bash
   git clone https://github.com/yourusername/goodbye-dpi-block-check.git
   cd goodbye-dpi-block-check
2. Copy blockcheck.py and strategies_gdpi.txt to the folder where GoodbyeDPI service is installed
3. Run blockcheck.py (e.g. from cmd.exe) with admin privileges
