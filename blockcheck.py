import subprocess
import requests
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# Constants for replacements
FAKE_SNI = "www.google.com"
FAKE_HEX = "5fc220bc088ae1a45235e46de591be50a50c979be92694471697a299ce78c1c276737bef7abc9668142b92c395810a659ff47dfd2411c010e990"
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6753.0 Safari/537.36'}
SITES_TO_TEST = [
    "https://discord.com",
    "https://discord.gg",
    "https://www.youtube.com",
    "https://rr1---sn-ug5onuxaxjvh-n8v6.googlevideo.com",
    "https://rr1---sn-gvnuxaxjvh-o8ge.googlevideo.com",
    "https://rr1---sn-ug5onuxaxjvh-p3ul.googlevideo.com",
    "https://rr1---sn-4axm-n8vs.googlevideo.com",
    "https://rr1---sn-nxu-nufl.googlevideo.com",
    "https://x.com",
    "https://instagram.com",
    "https://ntc.party",
    "https://rutracker.org",
    "https://anilibria.tv",
    "https://nyaa.land"
]

# Configure logging
def setup_logging():
    now = datetime.now()
    log_filename = f"log_blockcheck_GoodbyeDPI_{now.strftime('%d-%m-%Y_%H-%M-%S')}.txt"
    
    logging.basicConfig(
        filename=log_filename,
        level=logging.INFO,
        format='%(message)s'
    )

    # Also log to console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(message)s')
    console_handler.setFormatter(console_formatter)
    logging.getLogger().addHandler(console_handler)

def read_strategies(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file if not line.startswith('/')]

def replace_parameters(parameters):
    parameters = parameters.replace("FAKESNI", FAKE_SNI)
    parameters = parameters.replace("FAKEHEX", FAKE_HEX)
    return f"{parameters} -q"

def start_goodbyedpi(parameters):
    process = subprocess.Popen(['goodbyedpi.exe'] + parameters.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return process

def stop_goodbyedpi(process):
    process.terminate()
    process.wait()

def test_site(site):
    try:
        response = requests.get(site, headers = HEADERS, timeout=1)
        if len(response.content) == 0:
            return site, "NOT WORKING"
        return site, "WORKING"
    except requests.RequestException:
        return site, "NOT WORKING"

def test_sites():
    results = {}
    
    with ThreadPoolExecutor() as executor:
        future_to_site = {executor.submit(test_site, site): site for site in SITES_TO_TEST}
        for future in as_completed(future_to_site):
            site, status = future.result()
            results[site] = status

    return results

def log_results(params, results, current_line, total_lines):
    logging.info(f"Testing ({current_line}/{total_lines}): {params}")

    successes = 0
    for site, status in results.items():
        log_entry = f"{status}\t\t{site}"
        logging.info(log_entry)
        if status == "WORKING":
            successes += 1

    summary = f"Successes: {successes}/{len(results)}"
    logging.info(summary)

def main():
    setup_logging()
    strategies = read_strategies('strategies_gdpi.txt')
    total_lines = len(strategies)

    for current_line, original_params in enumerate(strategies, start=1):
        parameters = replace_parameters(original_params)
        process = start_goodbyedpi(parameters)

        # Allow some time for goodbyedpi.exe to start
        time.sleep(2)

        results = test_sites()
        log_results(parameters, results, current_line, total_lines)

        stop_goodbyedpi(process)

if __name__ == "__main__":
    main()