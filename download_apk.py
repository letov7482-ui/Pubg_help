import cloudscraper
import re
import os
import sys

scraper = cloudscraper.create_scraper(
    browser={'browser': 'chrome', 'platform': 'android', 'desktop': False}
)

# Паттерны — ищем ссылку с com.tencent.ig внутри
patterns = [
    r'href="(https?://[^"]*com\.tencent\.ig[^"]*\.apk[^"]*)"',
    r'href="(https?://[^"]*download[^"]*com\.tencent\.ig[^"]*)"',
    r'"downloadUrl"\s*:\s*"(https?://[^"]*com\.tencent\.ig[^"]*)"',
    r'data-dt-download-link="(https?://[^"]*com\.tencent\.ig[^"]*)"',
    r'href="([^"]*cdn[^"]*com\.tencent\.ig[^"]*)"',
    r'(https?://[^"\s>]*com\.tencent\.ig[^"\s<]*\.apk)',
    r'href="([^"]*\.apk[^"]*)"',
]

urls_to_try = [
    "https://apkcombo.com/pubg-mobile/com.tencent.ig/download/apk",
    "https://apkcombo.com/ru/pubg-mobile/com.tencent.ig/download/apk",
    "https://apkcombo.com/pubg-mobile/com.tencent.ig/old-versions/apk",
    "https://apkmirror.com/apk/tencent/pubg-mobile/pubg-mobile-4-6-0-release/pubg-mobile-4-6-0-android-apk-download/",
    "https://apk4fun.com/download/com.tencent.ig",
    "https://androidapksfree.com/apk/com-tencent-ig/",
]

for target in urls_to_try:
    try:
        print(f"\n{'='*60}")
        print(f"Trying: {target}")
        print(f"{'='*60}")
        
        page = scraper.get(target, timeout=30, headers={
            'Referer': 'https://www.google.com/',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        })
        
        print(f"Status: {page.status_code}, HTML size: {len(page.text)}")

        if page.status_code != 200:
            continue

        dl_url = None
        for pat in patterns:
            matches = re.findall(pat, page.text)
            for m in matches:
                # Фильтруем — не их установщик
                if 'apkcombo-installer' in m or 'installer' in m.lower():
                    continue
                # Приоритет ссылкам содержащим tencent или pubg
                if 'tencent' in m.lower() or 'pubg' in m.lower() or 'ig' in m.lower():
                    dl_url = m
                    print(f"  MATCH (priority): {m[:120]}")
                    break
                # Или просто большая ссылка
                elif len(m) > 50:
                    dl_url = m
                    print(f"  MATCH (fallback): {m[:120]}")
                    break
            if dl_url:
                break

        if not dl_url:
            # Ищем любые .apk ссылки в HTML
            all_apk = re.findall(r'href="([^"]*\.apk[^"]*)"', page.text)
            print(f"  All .apk links found: {len(all_apk)}")
            for link in all_apk[:10]:
                print(f"    -> {link[:120]}")
            
            # Ищем download кнопки
            dl_btns = re.findall(r'(?:href|action|src)="([^"]*download[^"]*)"', page.text, re.IGNORECASE)
            print(f"  Download links found: {len(dl_btns)}")
            for link in dl_btns[:10]:
                print(f"    -> {link[:120]}")
            
            # Ищем токены или скрытые ссылки
            tokens = re.findall(r'"(https?://[^"]*token[^"]*)"', page.text)
            if tokens:
                print(f"  Token URLs: {tokens[:5]}")

        if dl_url:
            # Если относительная ссылка — доделать
            if dl_url.startswith('/'):
                domain = target.split('/')[0] + '//' + target.split('/')[2]
                dl_url = domain + dl_url
            
            print(f"\n  DOWNLOADING: {dl_url[:150]}")
            
            r = scraper.get(dl_url, stream=True, timeout=600, headers={
                'Referer': target,
            })
            
            print(f"  Response status: {r.status_code}")
            
            if r.status_code == 200:
                total = 0
                with open("original.apk", "wb") as f:
                    for chunk in r.iter_content(chunk_size=1024*1024):
                        f.write(chunk)
                        total += len(chunk)
                
                size = os.path.getsize("original.apk")
                print(f"  Downloaded: {size} bytes ({size/1024/1024:.1f} MB)")
                
                if size > 10000000:
                    print("  SUCCESS")
                    sys.exit(0)
            else:
                print(f"  Bad status: {r.status_code}")
                # Попробуем сохранить HTML для отладки
                print(f"  Response preview: {r.text[:500]}")
        else:
            # Сохраняем HTML для анализа
            with open("debug_page.html", "w") as f:
                f.write(page.text)
            print("  No direct link. Saved page to debug_page.html")
            
            # Ищем все ссылки с .apk в любом виде
            all_apk_anywhere = re.findall(r'[\"\']([^\"\']*\.apk[^\"\']*)[\"\']', page.text)
            if all_apk_anywhere:
                print(f"  All .apk mentions: {len(all_apk_anywhere)}")
                for link in all_apk_anywhere[:15]:
                    print(f"    -> {link[:150]}")

    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        continue

# Финальная попытка — прямые CDN ссылки
print("\n" + "="*60)
print("Trying direct CDN URLs...")
print("="*60)

cdn_urls = [
    "https://download.pubgmobile.com/live/apk/com.tencent.ig.apk",
    "https://pubgmobile.download.prime cheating.garena.com/pubgm/apk/latest.apk",
]

for url in cdn_urls:
    try:
        print(f"\nTrying: {url}")
        r = scraper.get(url, stream=True, timeout=60)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
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
    except Exception as e:
        print(f"Error: {e}")

print("\nALL FAILED")
sys.exit(1)
