import os
import shutil
import requests
import hashlib
import json
import zipfile

def md5_checksum(file_path):
    """Calculate the MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def download_files(urls_file, download_folder):
    """Download files from URLs in the provided text file and create checksums.json."""
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)

    checksums = []  # List to hold checksum info

    with open(urls_file, 'r') as file:
        urls = file.readlines()

    for url in urls:
        url = url.strip()
        if not url:
            continue  # skip empty lines

        filename = os.path.basename(url)
        filepath = os.path.join(download_folder, filename)

        if url.startswith('file:///'):
            # Handle local file copying
            local_file_path = url[7:]  # Remove 'file://' prefix
            if os.path.exists(local_file_path):
                os.system(f'cp "{local_file_path}" "{filepath}"')  # Copy the local file
                md5sum = md5_checksum(filepath)  # Still calculate MD5 for local files
                checksums.append({
                    'file_name': filename,
                    'url': local_file_path,
                    'md5sum': md5sum
                })
            else:
                print(f"Local file not found: {local_file_path}")
            continue
        
        # Download the file from an online URL
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()  # Raise an error for bad responses
            with open(filepath, 'wb') as f:
                f.write(response.content)

            # Calculate MD5 checksum
            md5sum = md5_checksum(filepath)

            # Add to checksums list
            checksums.append({
                'file_name': filename,
                'url': url,
                'md5sum': md5sum
            })

        except Exception as e:
            print(f"Error downloading {url}: {e}")

    # Write checksums to a JSON file
    with open('checksums.json', 'w') as json_file:
        json.dump(checksums, json_file, indent=4)

def download_files_with_verification(download_folder):
    """Download files from URLs and verify their MD5 checksums."""
    with open('checksums.json', 'r') as json_file:
        checksums = json.load(json_file)

    for file_info in checksums:
        url = file_info['url']
        expected_md5 = file_info.get('md5sum')  # Check if md5sum exists
        filename = os.path.join(download_folder, file_info['file_name'])

        if url.startswith('file://'):
            # Handle local file copying again
            local_file_path = url[7:]  # Remove 'file://' prefix
            if os.path.exists(local_file_path):
                shutil.copy(local_file_path, filename)
                print(f"Copied local file: {filename}")
            else:
                print(f"Local file not found: {local_file_path}")
            continue
        
        # Download the file from an online URL
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            with open(filename, 'wb') as f:
                f.write(response.content)

        except Exception as e:
            print(f"Error downloading {url}: {e}")

        # Verify MD5 checksum if it exists
        calculated_md5 = md5_checksum(filename)
        if expected_md5 and expected_md5 != calculated_md5:
            os.remove(filename)
            raise RuntimeError(f"Checksum mismatch for {filename}: expected {expected_md5}, got {calculated_md5}")
        else:
            print(f"Successfully verified {filename}")

        if filename.endswith(".zip") and "goodbyedpi" in filename:
            extract_goodbyedpi(filename)



def extract_file_from_zip(zip_ref, file_to_extract, target_directory, target_filename):
    """Extracts a single file from a ZIP archive to a specified directory without preserving the original path."""
    if file_to_extract in zip_ref.namelist():
        with zip_ref.open(file_to_extract) as source_file:
            with open(os.path.join(target_directory, target_filename), 'wb') as target_file:
                target_file.write(source_file.read())
        print(f"Extracted {target_filename} from the ZIP file.")
    else:
        print(f"{file_to_extract} not found in the ZIP file.")

def extract_goodbyedpi(zip_name, bin_directory='bin'):
    """Extracts required files from the x86_64 directory of a ZIP file and removes the ZIP file afterward."""
    # Ensure the `bin` directory exists
    os.makedirs(bin_directory, exist_ok=True)

    # Check if the specified ZIP file exists and has a .zip extension
    if os.path.isfile(zip_name) and zip_name.endswith('.zip'):
        try:
            # Open the ZIP file
            with zipfile.ZipFile(zip_name, 'r') as zip_ref:
                # Define files to extract
                base_filename = os.path.splitext(os.path.basename(zip_name))[0]
                files_to_extract = {
                    f"{base_filename}/x86_64/goodbyedpi.exe": "goodbyedpi.exe",
                }

                # Extract each file
                for file_to_extract, target_filename in files_to_extract.items():
                    extract_file_from_zip(zip_ref, file_to_extract, bin_directory, target_filename)

            # Remove the ZIP file
            os.remove(zip_name)
            print(f"Removed the ZIP file: {zip_name}.")
        
        except Exception as e:
            print(f"Error extracting {zip_name}: {e}")
    else:
        print(f"{zip_name} is not a valid ZIP file.")

if __name__ == "__main__":
    g_absolute_path = os.path.dirname(os.path.abspath(__file__))
    download_folder = os.path.join(g_absolute_path, "bin")
    download_files_with_verification(download_folder)
