import signal
import subprocess
import aiohttp
import asyncio
import time
import logging
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import os
import sys

# Constants for replacements
FAKE_SNI = "www.google.com"
FAKE_HEX = "5fc220bc088ae1a45235e46de591be50a50c979be92694471697a299ce78c1c276737bef7abc9668142b92c395810a659ff47dfd2411c010e990"
PAYLOADTLS = "tls_clienthello_www_google_com.bin"
PAYLOADQUIC = "quic_initial_www_google_com.bin"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6753.0 Safari/537.36"}

ANTI_DPI_TOOLS_LIST = ["goodbyedpi", "zapret", "none"]
ZAPRET_NT_TOOL_NAME = "winws.exe"
ZAPRET_NT_PATH = "bin"
ZAPRET_NT_ARGS = ["--wf-l3=ipv4", "--wf-tcp=443"]
GOODBYEDPI_NT_TOOL_NAME = "goodbyedpi.exe"
GOODBYEDPI_NT_ARGS = []
GOODBYEDPI_NT_PATH = "bin"

zapret_linux_config_mounted = False
g_tool = ""
g_absolute_path = ""

def write_zapret_linux_config(args):
    global g_absolute_path
    os.makedirs(os.path.join(g_absolute_path, "tmp"), exist_ok=True)
    args_str = " ".join(args)
    config = open(os.path.join(g_absolute_path, "configs/zapret_linux_config"), "rb").read().decode("u8").replace('NFQWS_OPT_DESYNC_HTTPS="ARGS"', f'NFQWS_OPT_DESYNC_HTTPS="{args_str}"')
    open(os.path.join(g_absolute_path, "tmp/zapret_linux_config"), "wb").write(config.encode("u8"))

def remove_zapret_linux_config():
    global g_absolute_path
    os.remove(os.path.join(g_absolute_path, "tmp/zapret_linux_config"))

def mount_zapret_linux_config():
    global g_absolute_path
    config = os.path.join(g_absolute_path, "tmp/zapret_linux_config")
    subprocess.run(f"mount -o bind {config} /opt/zapret/config", shell=True)

def umount_zapret_linux_config():
    subprocess.run("umount /opt/zapret/config", shell=True)

def signal_handler(sig, frame):
    global g_tool
    """Handle signals to safely exit."""
    if g_tool == "zapret" and os.name == "posix":
        stop_tool(None, g_tool)
        sys.exit(0)

def find_tool_path(tool_name):
    if not tool_name in ANTI_DPI_TOOLS_LIST:
        raise RuntimeError(f"tool is not supported: {tool_name}")

    ret = ""
    if os.name == "nt":
        if tool_name == "zapret":
            ret = os.path.join(ZAPRET_NT_PATH, ZAPRET_NT_TOOL_NAME)
        elif tool_name == "goodbyedpi":
            ret = os.path.join(GOODBYEDPI_NT_PATH, GOODBYEDPI_NT_TOOL_NAME)
    else:
        if tool_name == "zapret":
            ret = os.path.join(ZAPRET_LINUX_PATH, ZAPRET_LINUX_TOOL_NAME)
        elif tool_name == "goodbyedpi":
            raise RuntimeError("GoodbyeDPI only supported on Windows")
    if not os.path.exists(ret):
        raise RuntimeError(f"Couldn't find specified tool at {ret}")
    return ret

def read_sites(set_name = "min"):
    global g_absolute_path
    file_path = os.path.join(g_absolute_path, f"sites_list/{set_name}.txt")
    with open(file_path, "r") as file:
        return [line.strip() for line in file if line.strip()]

def setup_logging(tool):
    global g_absolute_path
    now = datetime.now()
    log_filename = os.path.join(g_absolute_path, f"log_blockcheck_{tool}_{now.strftime('%d-%m-%Y_%H-%M-%S')}.txt")
    
    logging.basicConfig(
        filename=log_filename,
        level=logging.INFO,
        format="%(message)s"
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter("%(message)s")
    console_handler.setFormatter(console_formatter)
    logging.getLogger().addHandler(console_handler)

def read_strategies(tool_name, strategy_set_name = "min"):
    global g_absolute_path
    strategy_file = os.path.join(g_absolute_path, f"strategies/{tool_name}/{strategy_set_name}.txt")
    with open(strategy_file, "r") as file:
        return [line.strip() for line in file if not line.startswith("/")]

def replace_parameters(parameters):
    global g_absolute_path
    parameters = parameters.replace("FAKESNI", FAKE_SNI)
    parameters = parameters.replace("FAKEHEX", FAKE_HEX)
    parameters = parameters.replace("PAYLOADTLS", os.path.join(g_absolute_path, "bin", PAYLOADTLS))
    parameters = parameters.replace("PAYLOADQUIC", os.path.join(g_absolute_path, "bin", PAYLOADQUIC))
    return f"{parameters}"

def start_tool(tool, parameters):
    parameters = parameters.split()

    if os.name == "nt":
        if tool == "goodbyedpi":
            parameters = GOODBYEDPI_NT_ARGS + parameters
        elif tool == "zapret":
            parameters = ZAPRET_NT_ARGS + parameters
    else:
        if tool == "goodbyedpi":
            RuntimeError(f"tool {tool} is not supported on OS {os.name}")
        elif tool == "zapret":
            pass

    if (os.name == "posix" and tool == "zapret"):
        global zapret_linux_config_mounted
        if not zapret_linux_config_mounted:
            write_zapret_linux_config(parameters)
            mount_zapret_linux_config()
            zapret_linux_config_mounted = True
        subprocess.run(["/opt/zapret/init.d/sysv/zapret", "stop"], stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)
        subprocess.run(["/opt/zapret/init.d/sysv/zapret", "start"], stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)
        return
    else:
        tool_path = find_tool_path(tool)
        process = subprocess.Popen([tool_path] + parameters, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return process

def stop_tool(process, tool):
    if not (os.name == "posix" and tool == "zapret"):
        process.terminate()
        process.wait()
    else:
        global zapret_linux_config_mounted
        if zapret_linux_config_mounted:
            remove_zapret_linux_config()
            umount_zapret_linux_config()
            zapret_linux_config_mounted = False
        subprocess.run(["/opt/zapret/init.d/sysv/zapret", "stop"], stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)
        subprocess.run(["/opt/zapret/init.d/sysv/zapret", "start"], stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)

async def test_site(session, site, semaphore, timeout):
    async with semaphore:
        try:
            async with session.get(site, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                return site, "WORKING"
        except asyncio.CancelledError:
            return site, "CANCELLED"
        except Exception as e:
            return site, f"NOT WORKING"

async def test_sites(sites, timeout=2):
    results = {}
    async with aiohttp.ClientSession() as session:
        semaphore = asyncio.Semaphore(10)  # Limit to 10 concurrent requests
        tasks = [test_site(session, site, semaphore, timeout) for site in sites]
        completed_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in completed_results:
            if isinstance(result, Exception):
                results[result.args[0]] = "ERROR: " + str(result)
            else:
                results[result[0]] = result[1]

    return results

def log_results(params, results, current_line, total_lines):
    successes = 0
    for site, status in results.items():
        if status == "WORKING":
            successes += 1
            
    summary = f"Successes: {successes}/{len(results)}"
    logging.info(f"Testing ({current_line}/{total_lines}): {params}. {summary}")

    fmt_spaces_num = 8
    for site, status in results.items():
        if status == "WORKING":
            fmt_spaces_num = 12
        else:
            fmt_spaces_num = 8
        log_entry = f"{status}{' '*fmt_spaces_num}{site}"
        logging.info(log_entry)

def main():
    global g_tool, g_absolute_path

    g_absolute_path = os.path.dirname(os.path.abspath(__file__))
    
    if os.name == "posix":
        # Register signal handler for cleanup
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    parser = argparse.ArgumentParser(description="Block check script for GoodbyeDPI or Zapret.")
    parser.add_argument("--tool", type=str, choices=ANTI_DPI_TOOLS_LIST, required=True,
                        help="Choose anti-DPI tool: GoodbyeDPI, Zapret or none.")
        
    parser.add_argument('--strategies_set_name', type=str, default='simple', help='Name of the strategy set (basic, simple, min, medium or full, default: simple)')
    parser.add_argument('--sites_set_name', type=str, default='min', help='Name of the sites set (min or full, default: min)')
    parser.add_argument('--timeout', type=int, default=2, help='Timeout to load site (default: 2 sec)')
    
    args = parser.parse_args()
    g_tool = args.tool
    timeout = args.timeout
    
    sites = read_sites(set_name = args.sites_set_name)
    
    if not args.tool == "none":
        strategies = read_strategies(args.tool, args.strategies_set_name)
        total_lines = len(strategies)

    setup_logging(args.tool)

    if not args.tool == "none":
        for current_line, original_params in enumerate(strategies, start=1):
            parameters = replace_parameters(original_params)
            process = start_tool(args.tool, parameters)

            time.sleep(1.5)

            results = asyncio.run(test_sites(sites, timeout=timeout))
            log_results(parameters, results, current_line, total_lines)

            stop_tool(process, args.tool)
    else:
        results = asyncio.run(test_sites(sites, timeout=timeout))
        log_results("", results, "", 0)

if __name__ == "__main__":
    main()
