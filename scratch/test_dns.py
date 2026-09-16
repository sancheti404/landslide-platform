import time
import urllib.request

t0 = time.perf_counter()
urllib.request.urlopen('http://127.0.0.1:8000/health')
t_ip = (time.perf_counter() - t0) * 1000

t0 = time.perf_counter()
urllib.request.urlopen('http://localhost:8000/health')
t_lh = (time.perf_counter() - t0) * 1000

print(f"127.0.0.1: {t_ip:.2f} ms")
print(f"localhost: {t_lh:.2f} ms")
