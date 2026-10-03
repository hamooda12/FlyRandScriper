import time
import requests
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin

book_urls = []
unique_books = set()

url = "https://books.toscrape.com/catalogue/page-1.html"
page_num = 1

custom_headers = {
    "User-Agent": "FlyRankInternship-A9/1.0 (+ https://github.com/hamooda12/FlyRandScriper.git)"
}

while url is not None and page_num <= 3:

    file_path = Path(f"cache/catalogue-page-{page_num}.html")

    # -------------------------
    # FETCH / CACHE
    # -------------------------
    if file_path.is_file():
        print(f"CACHE HIT: page {page_num}")

        html = file_path.read_text(
            encoding="utf-8"
        )

    else:
        file_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        try:
            response = requests.get(
                url,
                timeout=5,
                headers=custom_headers
            )

            if response.status_code == 200:
                print(f"FETCH: page {page_num}")
                print(
                    "Response size:",
                    len(response.text)
                )

                html = response.text

                file_path.write_text(
                    html,
                    encoding="utf-8"
                )

            else:
                print(
                    "HTTP status:",
                    response.status_code
                )
                break

        except requests.exceptions.Timeout:
            print("The request timed out!")
            break

        # Delay only after a real request
        time.sleep(0.5)

    # -------------------------
    # PARSE
    # -------------------------
    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    books = soup.select(
        "article.product_pod"
    )

    # -------------------------
    # EXTRACT BOOK URLS
    # -------------------------
    for book in books:

        href = book.find("a").get("href")

        book_url = urljoin(
            url,
            href
        )

        book_urls.append(book_url)
        unique_books.add(book_url)

    print(
        "Page books:",
        len(books)
    )

    # -------------------------
    # FIND NEXT PAGE
    # -------------------------
    next_link = soup.select_one(
        ".pager .next a"
    )

    if next_link is not None:
        next_url = urljoin(
            url,
            next_link.get("href")
        )
    else:
        next_url = None

   
    url = next_url
    page_num += 1


# -------------------------
# FINAL REPORT
# -------------------------
print()
print("catalogue_pages:", page_num - 1)
print("discovered:", len(book_urls))
print("unique_urls:", len(unique_books))

for book in book_urls:
    print(book)