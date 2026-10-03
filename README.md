# A9 — The Polite Scraper

A small, polite web-scraping pipeline built as part of the FlyRank AI Fluency internship assignment.

The project scrapes books from Books to Scrape, a website designed as a sandbox for practicing web scraping.

## Target Classification

The website is:

https://books.toscrape.com/

I chose it because it is a public practice sandbox designed for learning web scraping.

The scope is:

- The first 3 catalogue pages only.
- Discover the book URLs from these pages.
- Visit the 60 discovered book pages.

Robots check: 404 Not Found — no robots file found.

### Why it is appropriate

Books to Scrape is a sandbox created for practicing scraping, so it is appropriate for this assignment.

I will not reuse this code on another site without checking its rules and terms first.

## What the Scraper Does

The scraper follows this pipeline:

```text
Fetch
  ↓
Extract
  ↓
Normalize
  ↓
Validate
  ↓
Store
  ↓
Report