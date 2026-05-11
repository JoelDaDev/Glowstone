import os
import json
import zipfile
import requests
from tqdm import tqdm

MANIFEST_URL = "https://launchermeta.mojang.com/mc/game/version_manifest_v2.json"

CACHE_DIR = "mc_assets"
JAR_PATH = os.path.join(CACHE_DIR, "client.jar")


def download_file(url, path):
    response = requests.get(url, stream=True)
    total = int(response.headers.get('content-length', 0))

    with open(path, "wb") as f, tqdm(
        desc=os.path.basename(path),
        total=total,
        unit='iB',
        unit_scale=True,
        unit_divisor=1024,
    ) as bar:
        for chunk in response.iter_content(chunk_size=8192):
            size = f.write(chunk)
            bar.update(size)


def get_latest_version():
    manifest = requests.get(MANIFEST_URL).json()
    return manifest["latest"]["release"]


def get_version_data(version_id):
    manifest = requests.get(MANIFEST_URL).json()
    for v in manifest["versions"]:
        if v["id"] == version_id:
            return requests.get(v["url"]).json()
    raise Exception("Version not found")


def extract_assets(jar_path, output_dir):
    with zipfile.ZipFile(jar_path, 'r') as jar:
        for file in jar.namelist():

            if file.endswith("/"):
                continue

            if not file.startswith("assets/minecraft/"):
                continue

            if any(x in file for x in [
                "blockstates/",
                "models/",
                "textures/"
            ]):
                target_path = os.path.join(output_dir, file)

                os.makedirs(os.path.dirname(target_path), exist_ok=True)

                with jar.open(file) as source, open(target_path, "wb") as target:
                    target.write(source.read())


def main():
    os.makedirs(CACHE_DIR, exist_ok=True)

    print("Getting latest version...")
    version = get_latest_version()
    print("Latest version:", version)

    print("Getting version metadata...")
    data = get_version_data(version)

    client_url = data["downloads"]["client"]["url"]

    print("Downloading client jar...")
    download_file(client_url, JAR_PATH)

    print("Extracting assets...")
    extract_assets(JAR_PATH, CACHE_DIR)

    print("Done!")
    print(f"Assets stored in: {CACHE_DIR}/assets/minecraft/")


if __name__ == "__main__":
    main()