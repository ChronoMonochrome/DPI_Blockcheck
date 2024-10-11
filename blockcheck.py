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
SITES_TO_TEST = list(set([
    "https://chess.com",
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
    "https://nyaa.land",
"https://rr1---sn-4axm-n8vs.googlevideo.com",
"https://rr1---sn-gvnuxaxjvh-o8ge.googlevideo.com",
"https://rr1---sn-ug5onuxaxjvh-p3ul.googlevideo.com",
"https://rr1---sn-ug5onuxaxjvh-n8v6.googlevideo.com",
"https://rr1---sn-gvnuxaxjvh-aome.googlevideo.com",
"https://rr2---sn-ubpouxgg5-n8ml.googlevideo.com",
"https://rr4---sn-q4flrnsl.googlevideo.com",
"https://rr10---sn-gvnuxaxjvh-304z.googlevideo.com",
"https://rr4---sn-n3toxu-axql.googlevideo.com",
"https://rr1---sn-jvhnu5g-n8ve7.googlevideo.com",
"https://rr14---sn-n8v7kn7r.googlevideo.com",
"https://rr16---sn-axq7sn76.googlevideo.com",
"https://rr1---sn-8ph2xajvh-5xge.googlevideo.com",
"https://rr1---sn-gvnuxaxjvh-5gie.googlevideo.com",
"https://rr12---sn-gvnuxaxjvh-bvwz.googlevideo.com",
"https://rr5---sn-n8v7knez.googlevideo.com",
"https://rr1---sn-u5uuxaxjvhg0-ocje.googlevideo.com",
"https://rr2---sn-q4fl6ndl.googlevideo.com",
"https://rr5---sn-gvnuxaxjvh-n8vk.googlevideo.com",
"https://rr4---sn-jvhnu5g-c35d.googlevideo.com",
"https://rr1---sn-q4fl6n6y.googlevideo.com",
"https://rr2---sn-hgn7ynek.googlevideo.com",
"https://www.youtube.com",
"https://x.com",
"https://video.google.com",
"https://youtu.be",
"https://yt.be",
"https://googleusercontent.com",
"https://yt3.ggpht.com",
"https://yt4.ggpht.com",
"https://googleapis.com",
"https://gstatic.com",
"https://play.google.com",
"https://kinozal.tv",
"https://hdkinoteatr.com",
"https://rutor.info",
"https://rutor.is",
"https://pixiv.net",
"https://danbooru.donmai.us",
"https://gelbooru.com",
"https://protonvpn.com",
"https://yande.re",
"https://pornhub.com",
"https://adguard.com",
"https://rutracker.org",
"https://gofile.io",
"https://readmanga.live",
"https://prostovpn.org",
"https://soundcloud.com",
"https://imagedelivery.net",
"https://meduza.io",
"https://nnmclub.to",
"https://facebook.com",
"https://fbcdn.net",
"https://fbsbx.com",
"https://checkvpn.net",
"https://quora.com",
"https://www.quora.com",
"https://novayagazeta.ru",
"https://muzlo.me",
"https://streamable.com",
"https://annas-archive.org",
"https://xhamster.com",
"https://10minutemail.net",
"https://patreon.com",
"https://torproject.org",
"https://psiphon.ca",
"https://amnezia.org",
"https://t.co",
"https://fb.com",
"https://linkedin.com",
"https://proton.me",
"https://thepiratebay.org",
"https://nnm-club-me.ru",
"https://10minutemail.com",
"https://www.instagram.com",
"https://instagram.com",
"https://mullvad.net",
"https://rezka.ag",
"https://xvideos.com",
"https://www.xv-ru.com",
"https://pcnews.ru",
"https://ohentai.org"
]))

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