import cloudscraper
import re
import os
import sys

scraper = cloudscraper.create_scraper(
    browser={'browser': 'chrome', 'platform': 'android', 'desktop': False}
)

urls_to_try = [
    "https://apkpure.com/pubg-mobile/com.tencent.ig/download?version=latest",
    "https://apkpure.net/pubg-mobile/com.tencent.ig/download?version=latest",
    "https://apkcombo.com/pubg-mobile/com.tencent.ig/download/apk",
    "https://www.apkmonk.com/app/com.tencent.ig/",
]

for target in urls_to_try:
    try:
        print(f"\n--- Trying: {target} ---")
        page = scraper.get(target, timeout=30)
        print(f"Status: {page.status_code}, Size: {len(page.text)}")

        if page.status_code != 200:
            continue

        patterns = [
            r'href="(https?://[^"]+\.apk[^"]*)"',
            r'data-dt-download-link="([^"]+)"',
            r'"downloadUrl"\s*:\s*"([^"]+)"',
            r'href="(/[^"]*download[^"]*\.apk[^"]*)"',
            r'href="(/download[^"]*)"',
            r'(https?://[^"\s]+\.apk)',
        ]

        dl_url = None
        for pat in patterns:
            matches = re.findall(pat, page.text)
            if matches:
                dl_url = matches[0]
                print(f"Found: {dl_url[:100]}")
                break

        if not dl_url:
            for pat in [r'href="(/download[^"]*)"', r'href="(/[^"]*\.apk[^"]*)"']:
                matches = re.findall(pat, page.text)
                if matches:
                    dl_url = "https://apkpure.com" + matches[0]
                    break

        if dl_url:
            print(f"Downloading from: {dl_url}")
            r = scraper.get(dl_url, stream=True, timeout=600)
            total = 0
            with open("original.apk", "wb") as f:
                for chunk in r.iter_content(chunk_size=1024*1024):
                    f.write(chunk)
                    total += len(chunk)
            size = os.path.getsize("original.apk")
            print(f"Downloaded: {size} bytes ({size/1024/1024:.1f} MB)")
            if size > 10000000:
                print("SUCCESS")
                sys.exit(0)
        else:
            print("No download link found")
            print("Page snippet:", page.text[:2000])

    except Exception as e:
        print(f"Error: {e}")
        continue

print("\nALL attempts failed")
sys.exit(1)
