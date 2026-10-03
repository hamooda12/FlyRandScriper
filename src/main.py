import requests
from pathlib import Path

url = "https://books.toscrape.com/catalogue/page-1.html"

custom_headers = {
    "User-Agent": "FlyRankInternship-A9/1.0 (+ https://github.com/hamooda12/FlyRandScriper.git)"
}

file_path = Path("cache/catalogue-page-1.html")

if file_path.is_file():
    print("CACHE HIT")
else:
    file_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        response = requests.get(
            url,
            timeout=5,
            headers=custom_headers
        )

        if response.status_code == 200:
            print("FETCH")
            print("Response size:", len(response.text))

            file_path.write_text(
                response.text,
                encoding="utf-8"
            )
        else:
            print("HTTP status:", response.status_code)

    except requests.exceptions.Timeout:
        print("The request timed out!")