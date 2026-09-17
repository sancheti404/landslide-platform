import urllib.request
import json

def check_urls():
    print("=== RUNTIME URL VERIFICATION ===")
    
    # 1. Check Spring Boot port 8080
    try:
        req = urllib.request.urlopen("http://localhost:8080/")
        sb_html = req.read().decode("utf-8", errors="ignore")
        print("[Spring Boot :8080]")
        print("  Status:", req.status)
        title_lines = [l.strip() for l in sb_html.splitlines() if "<title>" in l]
        print("  Title:", title_lines[0] if title_lines else "None")
        print("  Has Leaflet.js:", "leaflet.js" in sb_html)
        print("  Has React root (<div id=\"root\">):", 'id="root"' in sb_html)
    except Exception as e:
        print("  Spring Boot 8080 Error:", e)

    # 2. Check Vite port 5173
    try:
        req = urllib.request.urlopen("http://localhost:5173/")
        vite_html = req.read().decode("utf-8", errors="ignore")
        print("\n[Vite :5173 (Root /)]")
        print("  Status:", req.status)
        title_lines = [l.strip() for l in vite_html.splitlines() if "<title>" in l]
        print("  Title:", title_lines[0] if title_lines else "None")
        print("  Has React root (<div id=\"root\">):", 'id="root"' in vite_html)
        print("  Has /src/main.jsx:", "/src/main.jsx" in vite_html)
    except Exception as e:
        print("  Vite 5173 Error:", e)

    # 3. Check Vite SPA routes
    for route in ["/risk-map", "/assess", "/system"]:
        try:
            req = urllib.request.urlopen(f"http://localhost:5173{route}")
            print(f"\n[Vite :5173 ({route})]")
            print("  Status:", req.status)
            print("  Serves HTML for SPA:", "<div id=\"root\">" in req.read().decode("utf-8", errors="ignore"))
        except Exception as e:
            print(f"  Vite {route} Error:", e)

    # 4. Check Spring Boot for SPA routes (e.g. /risk-map)
    for route in ["/risk-map", "/assess"]:
        try:
            req = urllib.request.urlopen(f"http://localhost:8080{route}")
            print(f"\n[Spring Boot :8080 ({route})]")
            print("  Status:", req.status)
        except urllib.error.HTTPError as e:
            print(f"\n[Spring Boot :8080 ({route})]")
            print(f"  Status: {e.code} (Spring Boot does not have SPA forward controller for client-side React routes)")
        except Exception as e:
            print(f"  Spring Boot {route} Error:", e)

if __name__ == "__main__":
    check_urls()
