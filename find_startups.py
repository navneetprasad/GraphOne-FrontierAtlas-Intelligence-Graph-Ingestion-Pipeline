import httpx
import urllib.parse

def test_ds():
    candidates = [
        'RummageLabs/ycombinator_s2024',
        'mindthebridge/wizmap_startups_data',
        'kubston20004/YCombinatorv1_20260829_170045',
        'shreyaspimpalgaonkar/ycombinator_s24'
    ]
    for ds in candidates:
        encoded = urllib.parse.quote(ds, safe='')
        url = f"https://datasets-server.huggingface.co/rows?dataset={encoded}&config=default&split=train&offset=0&limit=5"
        try:
            r = httpx.get(url, timeout=10.0)
            print(f"{ds}: status={r.status_code}")
            if r.status_code == 200:
                rows = r.json().get('rows', [])
                if rows:
                    print("Keys:", list(rows[0]['row'].keys()))
                    print("Sample:", rows[0]['row'])
        except Exception as e:
            print(f"{ds}: {e}")

if __name__ == '__main__':
    test_ds()
