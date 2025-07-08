# jen_projects
miscellaneous projects

## project index

A collection of projects working on together and how to run them with example inputs

### 000_shoptalk_contact_scraper

This script processes a bunch of image screenshots and attempts to use OCR to make a tabular data format of information contained in the sequential image screenshots.

```
./install.sh
python3 process_images.py
```

### 001_csv_browser_use_example

This script processes a input csv file containing the output format from project 001 schema output.  The goal here is to identify the linkedin url for each individual (name, title, company) in the input csv.

```
./install.sh
python3 scrape_linked_in_url.py
```

