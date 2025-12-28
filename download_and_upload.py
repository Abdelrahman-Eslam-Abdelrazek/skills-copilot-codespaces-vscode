#!/usr/bin/env python3
"""Download videos from given URLs and upload to an FTP server (rpmshare style).

This script supports three input modes:
 - `--list links.txt` where the file contains lines `name|quality|url`.
 - `--item name,quality,url` repeated on the command line.
 - Interactive prompt: if neither `--list` nor `--item` are provided the script will ask
     you to paste entries one-per-line in the terminal (format `name|quality|url`).

FTP credentials can be embedded in the script via the DEFAULT_* constants below.
"""
import argparse
import os
import shutil
import subprocess
import sys
from urllib.parse import urlparse


# === Edit these defaults to embed your FTP credentials in the script ===
DEFAULT_FTP_HOST = "ftp://ftploadkdv.rpmup.site"
DEFAULT_FTP_USER = "ftp"
# WARNING: password stored in script plaintext per user request
DEFAULT_FTP_PASS = "MFA1RkpBdjhKUkRMbGZiWmdWbFR5RDNIS3VtQ1NWd1k1d1Z4eDM4UCtnPT06eXF6TUVPQU5ZSzQ4YXNhRU9BL0ZsZz09"
# ======================================================================

# === Additional known targets (add more as needed) ===
EARNVID_FTP_HOST = "ftp://earnvidsftp.com"
EARNVID_FTP_USER = "abdo722005"
EARNVID_FTP_PASS = "y6gi5lkl5t"
# ======================================================================


def which_binary(names):
    for n in names:
        p = shutil.which(n)
        if p:
            return p
    return None


def sanitize(s):
    return "".join(c if c.isalnum() or c in "-_." else "_" for c in s).strip("_")


def guess_ext_from_url(url):
    path = urlparse(url).path
    base = os.path.basename(path)
    if "." in base:
        return base.split(".")[-1]
    return "mp4"


def download(url, outpath):
    aria2 = which_binary(["aria2c"])
    if aria2:
        cmd = [aria2, "-x", "16", "-s", "16", "-o", os.path.basename(outpath), url]
        # Run in the destination dir so aria2 writes the filename
        print("Downloading with aria2:", url)
        subprocess.run(cmd, check=True, cwd=os.path.dirname(outpath) or ".")
    else:
        wget = which_binary(["wget"])
        if not wget:
            raise RuntimeError("Neither aria2c nor wget found; please install one to download files")
        print("Downloading with wget:", url)
        cmd = [wget, "-O", outpath, url]
        subprocess.run(cmd, check=True)


def upload_via_lftp(localpath, host, user, passwd, remote_dir):
    # Build lftp -u 'user','pass' host -e "mkdir -p remote_dir; cd remote_dir; put localpath; bye"
    if not shutil.which("lftp"):
        raise RuntimeError("lftp not found in PATH; please install lftp to upload files")

    remote_dir = remote_dir or "/"
    cmds = f"mkdir -p {remote_dir}; cd {remote_dir}; put {os.path.basename(localpath)}; bye"
    print(f"Uploading {localpath} -> {host}:{remote_dir}")
    # run from the file's directory so put uses the basename
    subprocess.run(["lftp", "-u", f"{user},{passwd}", host, "-e", cmds], check=True, cwd=os.path.dirname(localpath) or ".")


def process_entry(name, quality, url, workdir, ftp_host, ftp_user, ftp_pass, remote_dir, delete_after):
    name_s = sanitize(name)
    quality_s = sanitize(quality)
    ext = guess_ext_from_url(url)
    # filename format: name-quality.ext (e.g. ahmde-p720.mp4)
    outname = f"{name_s}-{quality_s}.{ext}"
    outpath = os.path.join(workdir, outname)

    # ensure workdir exists
    os.makedirs(workdir, exist_ok=True)

    # download to temporary filename if aria2 will write basename
    tempname = outpath
    try:
        download(url, tempname)
    except subprocess.CalledProcessError as e:
        print(f"Download failed for {url}: {e}", file=sys.stderr)
        return False

    # verify file exists
    if not os.path.exists(outpath):
        print(f"Downloaded file not found: {outpath}", file=sys.stderr)
        return False

    try:
        upload_via_lftp(outpath, ftp_host, ftp_user, ftp_pass, remote_dir)
    except subprocess.CalledProcessError as e:
        print(f"Upload failed for {outpath}: {e}", file=sys.stderr)
        return False

    if delete_after:
        try:
            os.remove(outpath)
        except Exception:
            pass

    return True


def parse_list_file(path):
    entries = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("|")
            if len(parts) < 3:
                print(f"Skipping invalid line (expect name|quality|url): {line}")
                continue
            name, quality, url = parts[0].strip(), parts[1].strip(), parts[2].strip()
            entries.append((name, quality, url))
    return entries


def main():
    parser = argparse.ArgumentParser(description="Download list of videos and upload to FTP")
    parser.add_argument("--list", help="Path to list file with lines name|quality|url")
    parser.add_argument("--item", action="append", help="Single item in format name,quality,url (can be repeated)")
    parser.add_argument("--workdir", default="downloads", help="Local download directory")
    # FTP args are optional — defaults can be embedded below
    parser.add_argument("--ftp-host", help="FTP host (optional if embedded in script)")
    parser.add_argument("--ftp-user", help="FTP user (optional if embedded in script)")
    parser.add_argument("--ftp-pass", help="FTP password (optional if embedded in script)")
    parser.add_argument("--remote-dir", default="/", help="Remote directory on FTP server")
    parser.add_argument("--target", choices=["rpmshare", "earnvid"], default="rpmshare", help="Preconfigured target to upload to (overridden by --ftp-* args)")
    parser.add_argument("--targets", help="Comma-separated preconfigured targets to upload to (e.g. rpmshare,earnvid). If provided overrides --target.")
    parser.add_argument("--delete-after-upload", action="store_true", help="Delete local file after successful upload")
    args = parser.parse_args()


    entries = []
    if args.list:
        entries.extend(parse_list_file(args.list))
    if args.item:
        for it in args.item:
            parts = it.split(",")
            if len(parts) < 3:
                print(f"Skipping invalid --item (expect name,quality,url): {it}")
                continue
            entries.append((parts[0].strip(), parts[1].strip(), parts[2].strip()))

    # If no entries provided via file/args, prompt interactively step-by-step
    if not entries:
        print("No entries supplied. Enter items step-by-step.")
        print("For each item you will be asked: name -> quality -> url")
        print("Leave the name empty to finish.")
        while True:
            try:
                name = input("Name (e.g. ahmde) [empty to finish]: ").strip()
            except EOFError:
                break
            if not name:
                break
            quality = input("Quality (e.g. p720 or 1080p): ").strip()
            url = input("URL: ").strip()
            if not url:
                print("URL required — skipping this entry.")
                continue
            entries.append((name, quality, url))

    if not entries:
        print("No entries to process. Provide --list or --item entries.")
        sys.exit(2)

    # check required binaries
    if not which_binary(["lftp"]):
        print("lftp not found in PATH. Please install lftp to enable FTP uploads.", file=sys.stderr)
        sys.exit(1)

    # Determine which preconfigured targets to use (single or multiple)
    if args.targets:
        selected_targets = [t.strip() for t in args.targets.split(",") if t.strip()]
    else:
        selected_targets = [args.target]

    # validate targets
    allowed = {"rpmshare", "earnvid"}
    for t in selected_targets:
        if t not in allowed:
            print(f"Unknown target: {t}", file=sys.stderr)
            sys.exit(2)

    # build a map of credentials per target, CLI --ftp-* (if provided) will override values for all selected targets
    targets_conf = {}
    for t in selected_targets:
        if t == "earnvid":
            h, u, p = EARNVID_FTP_HOST, EARNVID_FTP_USER, EARNVID_FTP_PASS
        else:
            h, u, p = DEFAULT_FTP_HOST, DEFAULT_FTP_USER, DEFAULT_FTP_PASS

        # apply CLI overrides if present (applies to every selected target)
        if args.ftp_host:
            h = args.ftp_host
        if args.ftp_user:
            u = args.ftp_user
        if args.ftp_pass:
            p = args.ftp_pass

        targets_conf[t] = (h, u, p)

    # validate credentials for targets
    for t, (h, u, p) in targets_conf.items():
        if not h or not u or not p:
            print(f"FTP credentials missing for target {t}: provide --ftp-* or set defaults in script.", file=sys.stderr)
            sys.exit(1)

    success_count = 0
    total = len(entries)
    failed_items = []

    for name, quality, url in entries:
        print(f"\nProcessing: name={name}, quality={quality}, url={url}")
        # attempt upload to each configured target
        per_target_results = {}
        for t, (h, u, p) in targets_conf.items():
            try:
                ok = process_entry(name, quality, url, args.workdir, h, u, p, args.remote_dir, args.delete_after_upload)
            except Exception as e:
                print(f"Error uploading to {t}: {e}", file=sys.stderr)
                ok = False
            per_target_results[t] = ok

        if all(per_target_results.values()):
            success_count += 1
        else:
            failed_items.append((name, per_target_results))

    print(f"\nDone. {success_count}/{total} items uploaded to all requested targets.")
    if failed_items:
        print("\nFailures:\n")
        for name, results in failed_items:
            bad = ", ".join([t for t, ok in results.items() if not ok])
            print(f" - {name}: failed targets -> {bad}")


if __name__ == "__main__":
    main()
