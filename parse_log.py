import argparse
import json
import os
import shutil

g_absolute_path = ""

def parse_log_file(file_path):
    configs = {}
    with open(file_path, 'r') as file:
        lines = [line.replace(" "*12, "\t").replace(" "*8, "\t") for line in file.readlines()]

    current_config = None
    current_sites = {}
    current_config_successes = ""

    for line in lines:
        line = line.strip()

        # Check for new configuration line
        if line.startswith("Testing"):
            if current_config:  # Save the last configuration if it exists
                configs[current_config] = (current_sites, current_config_successes)

            current_config_start_lst = line.split("):")[1].split(". Successes: ")
            current_config = current_config_start_lst[0]  # Get the configuration part
            current_config_successes = int(current_config_start_lst[1].split("/")[0])
            current_sites = {}
        elif line and current_config:
            status, site_name = line.split("\t")
            current_sites[site_name.strip()] = status.strip()

    # Don't forget to save the last configuration after the loop
    if current_config:
        configs[current_config] = (current_sites, current_config_successes)
    
    return configs


def find_working_sites(configs, tested_sites):
    working_sites_total = set()
    used_configs = {}

    for config, (site_status, current_config_successes) in configs.items():
        if "wssize" in config:
            # wssize can't work with a list of sites
            continue

        working_sites_current = {site for site, status in site_status.items() if status == "WORKING"}
        
        # Retain only working sites that haven't been covered
        new_working_sites = working_sites_current - working_sites_total
        
        if new_working_sites:
            # Update covered sites and record which config was used
            working_sites_total.update(new_working_sites)
            used_configs[config] = new_working_sites
            
            # Remove covered sites from the initial set
            tested_sites = tested_sites - new_working_sites
            
            # Stop if we've covered all initial sites
            if not tested_sites:
                break

    return working_sites_total, used_configs

def create_output_files(used_configs, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    strategies_folder = os.path.join(output_folder, "strategies")
    os.makedirs(strategies_folder, exist_ok=True)

    for config, sites in used_configs.items():
        sanitized_config_name = sanitize_config_name(config)
        sites_filename = os.path.join(strategies_folder, f"{sanitized_config_name}.txt")

        # Write the subset of sites to a file
        with open(sites_filename, 'w') as f:
            for site in sites:
                f.write(f"{site.replace('https://', '').replace('http://', '')}\n")

    if os.name == "nt":
        # Create start.cmd file
        cmd_file_path = os.path.join(output_folder, "start.cmd")
        with open(cmd_file_path, 'w') as f:
            f.write("set BIN=%~dp0bin\\\n")
            f.write("set STRAT=%~dp0strategies\\\n\n")
            f.write('start "Zapret: multi" /min "%BIN%winws.exe" ^\n')
            f.write('--wf-tcp=80,443 --wf-udp=443,50000-50099 ^\n')
            
            for i, (config, sites) in enumerate(used_configs.items()):
                sanitized_config_name = sanitize_config_name(config)
                f.write(f'--filter-tcp=443 --hostlist="%STRAT%{sanitized_config_name}.txt" {config} --new ^\n')
            f.write('--filter-udp=443 --hostlist="%~dp0list-discord.txt" --dpi-desync=fake --dpi-desync-repeats=6 --dpi-desync-udplen-increment=10 --dpi-desync-udplen-pattern=0xDEADBEEF --dpi-desync-fake-quic="%BIN%quic_initial_www_google_com.bin" --new ^\n')
            f.write('--filter-udp=50000-50099 --dpi-desync=fake --dpi-desync-any-protocol --dpi-desync-cutoff=d3 --dpi-desync-repeats=6 --dpi-desync-fake-quic="%BIN%quic_initial_www_google_com.bin" --new ^\n')
            f.write('--filter-tcp=443 --hostlist="%~dp0list-discord.txt" --dpi-desync=fake,split --dpi-desync-autottl=2 --dpi-desync-repeats=6 --dpi-desync-fooling=badseq --dpi-desync-fake-tls="%BIN%tls_clienthello_www_google_com.bin" --new ^\n')
            f.write('--filter-udp=443 --hostlist="%~dp0list-general.txt" --dpi-desync=fake --dpi-desync-repeats=6 --dpi-desync-udplen-increment=10 --dpi-desync-udplen-pattern=0xDEADBEEF --dpi-desync-fake-quic="%BIN%quic_initial_www_google_com.bin" --new ^\n')
            f.write('--filter-tcp=80 --hostlist="%~dp0list-general.txt" --dpi-desync=fake,split2 --dpi-desync-autottl=2 --dpi-desync-fooling=md5sig --new ^\n')
            f.write('--filter-tcp=443 --hostlist-auto="%STRAT%hostlist-auto.txt" --hostlist="%~dp0list-general.txt" --dpi-desync=fake,split --dpi-desync-autottl=2 --dpi-desync-repeats=6 --dpi-desync-fooling=badseq --dpi-desync-fake-tls="%BIN%tls_clienthello_www_google_com.bin"\n')
    else:
        desync_https_args = ""
        for i, (config, sites) in enumerate(used_configs.items()):
            sanitized_config_name = sanitize_config_name(config)
            strat_path = os.path.join(os.path.realpath(output_folder), "strategies", sanitized_config_name)
            if i != len(used_configs) - 1:
                desync_https_args += f"{config} --hostlist={strat_path}.txt --new "
            else:
                desync_https_args += f"{config} --hostlist={strat_path}.txt"

        linux_config_path = os.path.join(g_absolute_path, "configs/zapret_linux_config")
        new_config = open(linux_config_path, "rb").read().decode("u8").replace('NFQWS_OPT_DESYNC_HTTPS="ARGS"', f'NFQWS_OPT_DESYNC_HTTPS="{desync_https_args}"')
        open(os.path.join(os.path.realpath(output_folder), "config"), "wb").write(new_config.encode("u8"))
        

def sanitize_config_name(config_name):
    # Replace spaces and equal signs with underscores
    sanitized = config_name.replace(" ", "_").replace("=", "_").replace("/", "_").replace("-", "")
    return sanitized
    
def create_cmd(configs, output_dir):
    tested_sites = set(list(configs.values())[0][0])

    # Find the working sites and the configs used
    working_sites, used_configs = find_working_sites(configs, tested_sites.copy())

    # Output results
    print("Working sites:", working_sites)
    print("Used configurations for each subset:")
    for config, sites in used_configs.items():
        print(f"{config}: {sites}")

    print("Not working sites:", tested_sites - working_sites)
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)
    bin_folder = os.path.join(g_absolute_path, 'bin')
    # Copy the `bin` folder to the output directory
    if os.path.exists(bin_folder):
        shutil.copytree(bin_folder, os.path.join(output_dir, 'bin'), dirs_exist_ok=True)
    else:
        print(f"Warning: 'bin' folder does not exist in the script directory: {bin_folder}")

    shutil.copy(os.path.join(g_absolute_path, "sites_list", "list-discord.txt"), output_dir)
    shutil.copy(os.path.join(g_absolute_path, "sites_list", "list-general.txt"), output_dir)
    # Create output files using the specified output directory
    create_output_files(used_configs, output_dir)

def sort_configs(configs, output_file, output_format, configs_num):
    sorted_configs = {k: v[1] for (k, v) in sorted(configs.items(), key=lambda item: item[1][1], reverse=True)}
    if output_format == "json":
        if not "." in output_file:
            output_file += ".json"
        with open(output_file, "w", encoding='utf8') as json_file:
            json.dump(configs, json_file, ensure_ascii=False, indent=4)
    elif output_format == "stdout":
        print(f"List of {configs_num} best found configurations:")
        sites_total = len(list(configs.values())[0][0])
        configs = list(sorted_configs.items())[:configs_num]
        for config, successes in configs:
            print(f"{config} (successes: {successes}/{sites_total})")

def main():
    global g_absolute_path
    # Set up the argument parser
    parser = argparse.ArgumentParser(description="Process log files for site coverage.")
    parser.add_argument('-i', '--input-log-file', required=True, help="Path to the input log file.")
    parser.add_argument('-m', '--mode', type=str, choices=["create_cmd", "sort_configs"], default="create_cmd", help="What to do with the parsed log (create cmd file or sort configs by amount of successes, default \"create_cmd\").")
    parser.add_argument('-f', '--format', type=str, choices=["stdout", "json"], default="stdout", help="Output file format (stdout, json), default: print to stdout.")
    parser.add_argument('-n', '--configs_num', type=int, default=10, help="Limit amount of printed best found configurations to this number.")
    parser.add_argument('-o', '--output', default="dist", help="Output path (default: 'dist').")
    
    # Parse the arguments
    args = parser.parse_args()
    
    log_file_path = args.input_log_file

    # Determine the script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    g_absolute_path = script_dir

    # Parse the log file
    configs = parse_log_file(log_file_path)

    if args.mode == "create_cmd":
        create_cmd(configs, args.output)
    elif args.mode == "sort_configs":
        sort_configs(configs, args.output, args.format, args.configs_num)

if __name__ == "__main__":
    main()
