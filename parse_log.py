import argparse
import os
import shutil

def parse_log_file(file_path):
    configs = {}
    with open(file_path, 'r') as file:
        lines = [line.replace(" "*12, "\t").replace(" "*8, "\t") for line in file.readlines()]

    current_config = None
    current_sites = {}

    for line in lines:
        line = line.strip()

        # Check for new configuration line
        if line.startswith("Testing"):
            if current_config:  # Save the last configuration if it exists
                configs[current_config] = current_sites

            current_config = line.split("):")[1].split(". Successes")[0]  # Get the configuration part
            current_sites = {}
        elif line and current_config:
            status, site_name = line.split("\t")
            current_sites[site_name.strip()] = status.strip()

    # Don't forget to save the last configuration after the loop
    if current_config:
        configs[current_config] = current_sites
    
    return configs


def find_working_sites(configs, initial_sites):
    covered_sites = set()
    used_configs = {}  # Dictionary to store used configs for each subset

    for config, site_status in configs.items():
        if "wssize" in config:
            # wssize can't work with a list of sites
            continue

        working_sites = {site for site, status in site_status.items() if status == "WORKING"}
        
        # Retain only working sites that haven't been covered
        new_working_sites = working_sites - covered_sites
        
        if new_working_sites:
            # Update covered sites and record which config was used
            covered_sites.update(new_working_sites)
            used_configs[config] = new_working_sites
            
            # Remove covered sites from the initial set
            initial_sites = initial_sites - new_working_sites
            
            # Stop if we've covered all initial sites
            if not initial_sites:
                break

    return covered_sites, used_configs

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

def sanitize_config_name(config_name):
    # Replace spaces and equal signs with underscores
    sanitized = config_name.replace(" ", "_").replace("=", "_").replace("-", "")
    return sanitized

def main():
    # Set up the argument parser
    parser = argparse.ArgumentParser(description="Process log files for site coverage.")
    parser.add_argument('-i', '--input-log-file', required=True, help="Path to the input log file.")
    parser.add_argument('-o', '--output-dir', default="dist", help="Output directory (default: 'dist').")
    
    # Parse the arguments
    args = parser.parse_args()
    
    log_file_path = args.input_log_file
    output_dir = args.output_dir

    # Determine the script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    bin_folder = os.path.join(script_dir, 'bin')

    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Copy the `bin` folder to the output directory
    if os.path.exists(bin_folder):
        shutil.copytree(bin_folder, os.path.join(output_dir, 'bin'), dirs_exist_ok=True)
    else:
        print(f"Warning: 'bin' folder does not exist in the script directory: {bin_folder}")

    shutil.copy(os.path.join(script_dir, "sites_list", "list-discord.txt"), output_dir)
    shutil.copy(os.path.join(script_dir, "sites_list", "list-general.txt"), output_dir)

    # Parse the log file
    configs = parse_log_file(log_file_path)

    # Extract initial sites from the first configuration
    initial_sites = set(list(configs.values())[0])

    # Find the working sites and the configs used
    covered_sites, used_configs = find_working_sites(configs, initial_sites.copy())

    # Output results
    print("Covered Sites:", covered_sites)
    print("Used Configurations for Each Subset:")
    for config, sites in used_configs.items():
        print(f"{config}: {sites}")

    print("Remaining Sites:", initial_sites - covered_sites)
    
    # Create output files using the specified output directory
    create_output_files(used_configs, output_dir)

if __name__ == "__main__":
    main()