import time
import json
import requests

from pathlib import Path
from datetime import datetime, timezone

from pydantic import BaseModel
from bs4 import BeautifulSoup
from urllib.parse import urljoin


# =========================================================
# PYDANTIC SCHEMA
# =========================================================

class Book(BaseModel):
    title: str
    product_url: str
    price_text: str
    price_gbp: float
    availability_text: str
    rating_text: str
    description: str | None
    source_page: str
    fetched_at: str


# =========================================================
# CONFIGURATION
# =========================================================

BASE_URL = "https://books.toscrape.com/catalogue/page-1.html"

custom_headers = {
    "User-Agent": (
        "FlyRankInternship-A9/1.0 "
        "(+ https://github.com/hamooda12/FlyRandScriper.git)"
    )
}


# =========================================================
# RUN REPORT VARIABLES
# =========================================================

run_start = datetime.now(timezone.utc)

pages_fetched = 0
cache_hits = 0

valid_records = 0
invalid_records = 0

failed_pages = []


# =========================================================
# STAGE 2 — DISCOVER BOOK URLs
# =========================================================

book_urls = []
unique_books = set()

# Book URL -> catalogue page
book_source_pages = {}

url = BASE_URL
page_num = 1


while url is not None and page_num <= 3:

    file_path = Path(
        f"cache/catalogue-page-{page_num}.html"
    )

    # -----------------------------------------------------
    # CACHE
    # -----------------------------------------------------

    if file_path.is_file():

        print(
            f"CACHE HIT: catalogue page {page_num}"
        )

        cache_hits += 1

        html = file_path.read_text(
            encoding="utf-8"
        )

    # -----------------------------------------------------
    # FETCH
    # -----------------------------------------------------

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

                print(
                    f"FETCH: catalogue page {page_num}"
                )

                print(
                    "Response size:",
                    len(response.text)
                )

                html = response.text

                file_path.write_text(
                    html,
                    encoding="utf-8"
                )

                pages_fetched += 1

            else:

                print(
                    "HTTP status:",
                    response.status_code
                )

                failed_pages.append({
                    "url": url,
                    "status_code": response.status_code,
                    "type": "catalogue"
                })

                break

        except requests.exceptions.Timeout:

            print(
                f"Timeout: catalogue page {page_num}"
            )

            failed_pages.append({
                "url": url,
                "error": "timeout",
                "type": "catalogue"
            })

            break

        time.sleep(0.5)


    # -----------------------------------------------------
    # PARSE
    # -----------------------------------------------------

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    books = soup.select(
        "article.product_pod"
    )


    # -----------------------------------------------------
    # EXTRACT BOOK URLS
    # -----------------------------------------------------

    for book in books:

        href = book.find("a").get("href")

        book_url = urljoin(
            url,
            href
        )

        book_urls.append(
            book_url
        )

        unique_books.add(
            book_url
        )

        book_source_pages[book_url] = url


    print(
        "Page books:",
        len(books)
    )


    # -----------------------------------------------------
    # NEXT PAGE
    # -----------------------------------------------------

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


# =========================================================
# CATALOGUE REPORT
# =========================================================

catalogue_pages = page_num - 1

print()

print(
    "catalogue_pages:",
    catalogue_pages
)

print(
    "discovered:",
    len(book_urls)
)

print(
    "unique_urls:",
    len(unique_books)
)


# =========================================================
# STAGE 3 + 4 + 5 — DETAIL PAGES
# =========================================================

records = []

valid_books = []

errors = []

book_num = 1


for book_url in book_urls:
    
    file_path = Path(
        f"books/book-number-{book_num}.html"
    )

    html = None
    success = False


    # =====================================================
    # CACHE
    # =====================================================

    if file_path.is_file():

        print(
            f"CACHE HIT: book {book_num}"
        )

        cache_hits += 1

        html = file_path.read_text(
            encoding="utf-8"
        )

        success = True


    # =====================================================
    # FETCH WITH RETRY
    # =====================================================

    else:

        file_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        for attempt in range(2):

            try:

                print(
                    f"FETCH: book {book_num} "
                    f"(attempt {attempt + 1})"
                )

                response = requests.get(
                    book_url,
                    timeout=5,
                    headers=custom_headers
                )


                # -----------------------------------------
                # SUCCESS
                # -----------------------------------------

                if response.status_code == 200:

                    print(
                        "Response size:",
                        len(response.text)
                    )

                    html = response.text

                    file_path.write_text(
                        html,
                        encoding="utf-8"
                    )

                    pages_fetched += 1

                    success = True

                    break


                # -----------------------------------------
                # SERVER ERROR → RETRY
                # -----------------------------------------

                elif 500 <= response.status_code < 600:

                    print(
                        f"Server error "
                        f"{response.status_code}"
                    )

                    if attempt == 0:

                        print(
                            "Retrying..."
                        )

                        time.sleep(0.5)

                        continue

                    else:

                        print(
                            "Second attempt failed."
                        )

                        failed_pages.append({
                            "url": book_url,
                            "status_code": response.status_code,
                            "type": "detail"
                        })

                        break


                # -----------------------------------------
                # 403 / 404 / OTHER → NO RETRY
                # -----------------------------------------

                else:

                    print(
                        "HTTP status:",
                        response.status_code
                    )

                    failed_pages.append({
                        "url": book_url,
                        "status_code": response.status_code,
                        "type": "detail"
                    })

                    break


            except requests.exceptions.Timeout:

                print(
                    "Timeout"
                )

                if attempt == 0:

                    print(
                        "Retrying..."
                    )

                    time.sleep(0.5)

                    continue

                else:

                    print(
                        "Second attempt timed out."
                    )

                    failed_pages.append({
                        "url": book_url,
                        "error": "timeout",
                        "type": "detail"
                    })

                    break


            except requests.exceptions.RequestException as e:

                print(
                    "Request error:",
                    str(e)
                )

                failed_pages.append({
                    "url": book_url,
                    "error": str(e),
                    "type": "detail"
                })

                break


    # =====================================================
    # IF BOTH ATTEMPTS FAILED
    # =====================================================

    if not success:

        errors.append({
            "product_url": book_url,
            "error": "Failed to fetch page"
        })

        invalid_records += 1

        book_num += 1

        continue


    # =====================================================
    # PARSE DETAIL PAGE
    # =====================================================

    soup = BeautifulSoup(
        html,
        "html.parser"
    )


    # =====================================================
    # TITLE
    # =====================================================

    title_element = soup.find("h1")

    title = (
        title_element.get_text(strip=True)
        if title_element
        else None
    )


    # =====================================================
    # PRICE
    # =====================================================

    price_element = soup.select_one(
        ".price_color"
    )

    price_text = (
        price_element.get_text(strip=True)
        if price_element
        else None
    )


    if price_text:

        price_gbp = float(
            price_text[2:]
        )

    else:

        price_gbp = None


    # =====================================================
    # AVAILABILITY
    # =====================================================

    availability_element = soup.select_one(
        "p.instock"
    )

    availability_text = (
        availability_element.get_text(strip=True)
        if availability_element
        else None
    )


    # =====================================================
    # RATING
    # =====================================================

    rating_element = soup.select_one(
        "p.star-rating"
    )

    if rating_element:

        rating_classes = rating_element.get(
            "class",
            []
        )

        rating_text = next(
            (
                item
                for item in rating_classes
                if item != "star-rating"
            ),
            None
        )

    else:

        rating_text = None


    # =====================================================
    # DESCRIPTION
    # =====================================================

    description_header = soup.select_one(
        "#product_description"
    )

    if description_header:

        description_element = (
            description_header.find_next_sibling("p")
        )

        if description_element:

            description = (
                description_element.get_text(
                    strip=True
                )
            )

        else:

            description = None

    else:

        description = None


    # =====================================================
    # SOURCE PAGE
    # =====================================================

    source_page = book_source_pages.get(
        book_url
    )


    # =====================================================
    # FETCHED AT
    # =====================================================

    fetched_at = datetime.now(
        timezone.utc
    ).isoformat()


    # =====================================================
    # RAW + NORMALIZED RECORD
    # =====================================================

    record = {

        "title": title,

        "product_url": book_url,

        "price_text": price_text,

        "availability_text": availability_text,

        "rating_text": rating_text,

        "description": description,

        "source_page": source_page,

        "fetched_at": fetched_at,

        "price_gbp": price_gbp
    }


    records.append(
        record
    )


    # =====================================================
    # PYDANTIC VALIDATION
    # =====================================================

    try:

        book = Book(
            **record
        )

        valid_books.append(
            book.model_dump()
        )

        valid_records += 1


    except Exception as e:

        errors.append({
            "product_url": book_url,
            "error": str(e)
        })

        invalid_records += 1


    # =====================================================
    # FIRST RECORD OUTPUT
    # =====================================================

    if book_num == 1:

        print()
        print(
            "FIRST BOOK RECORD"
        )
        print(
            "-----------------"
        )

        for key, value in record.items():

            print(
                f"{key}: {value}"
            )

        print()


    book_num += 1

# =========================================================
# SAVE books.json
# =========================================================

with open(
    "books.json",
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        valid_books,
        file,
        ensure_ascii=False,
        indent=2
    )


# =========================================================
# SAVE errors.json
# =========================================================

with open(
    "errors.json",
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        errors,
        file,
        ensure_ascii=False,
        indent=2
    )


# =========================================================
# RUN REPORT
# =========================================================

run_end = datetime.now(
    timezone.utc
)

duration = (
    run_end - run_start
).total_seconds()


run_report = {

    "start_time": run_start.isoformat(),

    "duration_seconds": duration,

    "pages_fetched": pages_fetched,

    "cache_hits": cache_hits,

    "valid_records": valid_records,

    "invalid_records": invalid_records,

    "failed_pages": failed_pages
}


# =========================================================
# SAVE run-report.json
# =========================================================

with open(
    "run-report.json",
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        run_report,
        file,
        ensure_ascii=False,
        indent=2
    )


# =========================================================
# FINAL REPORT
# =========================================================

print()
print(
    "================================="
)
print(
    "FINAL RUN REPORT"
)
print(
    "================================="
)

print(
    "catalogue_pages:",
    catalogue_pages
)

print(
    "discovered:",
    len(book_urls)
)

print(
    "unique_urls:",
    len(unique_books)
)

print(
    "detail_pages:",
    len(records)
)

print(
    "valid_records:",
    valid_records
)

print(
    "invalid_records:",
    invalid_records
)

print(
    "failed_pages:",
    len(failed_pages)
)

print(
    "cache_hits:",
    cache_hits
)

print(
    "pages_fetched:",
    pages_fetched
)

print(
    "duration_seconds:",
    duration
)

print(
    "================================="
)