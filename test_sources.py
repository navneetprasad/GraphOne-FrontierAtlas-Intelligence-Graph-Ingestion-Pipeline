import httpx
import json

def test_pwc_redirect():
    print("Testing Papers With Code with follow_redirects...")
    url = "https://paperswithcode.com/api/v1/papers/?items_per_page=50"
    with httpx.Client(timeout=20.0, follow_redirects=True) as client:
        r = client.get(url)
        print("PWC status:", r.status_code)
        if r.status_code == 200:
            data = r.json()
            print(f"PWC total papers: {data.get('count')}, returned: {len(data.get('results', []))}")
            if data.get('results'):
                sample = data['results'][0]
                print("Title:", sample.get("title"))
                print("Paper URL:", sample.get("url_abs") or f"https://arxiv.org/abs/{sample.get('arxiv_id')}")
                print("Authors:", sample.get("authors"))
                print("Paper ID for repositories:", sample.get("id"))
                paper_id = sample.get("id")
                repo_url = f"https://paperswithcode.com/api/v1/papers/{paper_id}/repositories/"
                repo_r = client.get(repo_url)
                print(f"Repo query status for paper {paper_id}:", repo_r.status_code)
                if repo_r.status_code == 200:
                    repo_data = repo_r.json()
                    print("Repo count:", repo_data.get("count"))
                    if repo_data.get("results"):
                        print("Sample repo:", repo_data["results"][0])

def test_arxiv():
    print("\nTesting Arxiv API...")
    url = "https://export.arxiv.org/api/query?search_query=cat:cs.AI+OR+cat:cs.LG+OR+cat:cs.CL&start=0&max_results=20"
    with httpx.Client(timeout=20.0, follow_redirects=True) as client:
        r = client.get(url)
        print("Arxiv status:", r.status_code, "Length:", len(r.text))
        import xml.etree.ElementTree as ET
        root = ET.fromstring(r.text)
        ns = {'atom': 'http://www.w3.org/2005/Atom', 'arxiv': 'http://arxiv.org/schemas/atom'}
        entries = root.findall('atom:entry', ns)
        print("Arxiv entries found:", len(entries))
        if entries:
            title = entries[0].find('atom:title', ns).text.strip()
            published = entries[0].find('atom:published', ns).text.strip()
            print("First Arxiv Title:", title)
            print("Published:", published)

if __name__ == "__main__":
    test_pwc_redirect()
    test_arxiv()
