"""Web crawler for Rackham site that takes list of document names as input, and outputs a file with
all document names and what page the document is linked on. If the document is not linked on any pages,
no page URL will be outputted alongside the page.

Purpose: find files on site still in use, and remove any documents from database no longer in use on the site.

Written by Rachel Cheng, Jun 2023."""

import sys
import os
import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import logging

# log output if desired 
LOGGER = logging.getLogger(__name__)
logging.basicConfig(level = logging.INFO)


def main():
    output_log_filename = "output_log.txt"
    with open(output_log_filename, 'w') as output_log:
        output_log.write("Program starting...\n\n")
    LOGGER.info("Program starting...\n\n")

    # grab args from command line:
    #   first arg: name of file containing seed URL (rackham.umich.edu in this case)
    #   second arg: input documents whose page source is to be found
    seed_filename = sys.argv[1]
    input_docs_filename = sys.argv[2]

    # headers to be able to make GET request
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36',
        'referer': 'https://...'
    }

    # initialize URL frontier with seed URLs, and add seed URLs to acceptable domain list
    acceptable_domains = []
    potential_url_frontier = []
    with open(seed_filename) as seed_doc:
        seed_urls = seed_doc.read().splitlines()
        for url in seed_urls:
            # adding to URL frontier
            potential_url_frontier.append(url)
            # adding to acceptable domain list
            domain_name = urlparse(url)
            acceptable_domains.append(domain_name.netloc)

    with open(output_log_filename, 'a') as output_log:
        output_log.write(f"Acceptable domain(s) to crawl: {acceptable_domains}\n")
    # LOGGER.info(f"Acceptable domain(s) to crawl: {acceptable_domains}\n")

    # get filenames of input documents
    files_to_be_found = {}
    with open(input_docs_filename) as input_files:
        input_filenames = input_files.read().splitlines()
        # initialize value of each filename as empty list of parent pages
        for filename in input_filenames:
            files_to_be_found[filename] = set()

    # LOGGER.info(f"Seed URL(s): {potential_url_frontier}\nDocument(s) to be found on site: {files_to_be_found.keys()}")

    # sets to prevent crawl loops
    identified_links = set() # links that have already been identified
    visited_links = set() # links whose pages have already been scraped

    # put seed URLs through URL filter
    url_frontier = []
    for url in potential_url_frontier:
        # remove www from link
        url = url.replace("www.","")

        # make all links have https protocol
        parsed_url = urlparse(url)
        parsed_url = parsed_url._replace(fragment="")
        parsed_url = parsed_url._replace(scheme="https")
        
        with open(output_log_filename, 'a') as output_log:
            output_log.write(f"====={parsed_url.geturl()}=====\n")
        LOGGER.info(f"====={parsed_url.geturl()}=====")

        # check if url is within acceptable domain(s), also removing "www" from domain to normalize
        within_domain = False
        for domain in acceptable_domains:
            if domain == parsed_url.netloc:
                within_domain = True
                break
        
        if not within_domain:
            with open(output_log_filename, 'a') as output_log:
                output_log.write(f"Not within domain - moving to next potential URL\n")
            # LOGGER.info(f"Not within domain - moving to next potential URL\n")
            continue

        # check if link is html (non-document URLs)
        r = requests.head(parsed_url.geturl())
        if "text/html" not in r.headers["content-type"]:
            continue
            
        # check for duplicate
        if parsed_url.geturl() in identified_links:
            continue
            
        # add to identified links list + url frontier
        identified_links.add(parsed_url.geturl())
        url_frontier.append(parsed_url.geturl())

    # until URL frontier empty, check for 2 things:
    #   1. non-document URLs that pass URL filter should be added to identified links list
    #   2. URLs pointing to a downloads folder with a document, checked against existing input docs for match
    while len(url_frontier) > 0:
        # pop URL from front of URL frontier
        current_url = url_frontier.pop(0)

        # if url already visited, continue loop
        if current_url in visited_links:
            continue

        # download page (P)
        try:
            response = requests.get(current_url, headers=headers)
        except:
            continue

        # if cannot download P, continue loop.
        if response.status_code != 200:
            continue

        # if downloadable, add to list of visited links
        visited_links.add(current_url)

        # Parse P to obtain list of new links N.
        soup = BeautifulSoup(response.text, 'html.parser')
        for link in soup.find_all('a'):
            # get url
            potential_url = link.get('href')
            if (potential_url == None):
                # LOGGER.info("status: url of NONE type\n")
                continue
        
            # remove whitespace if it exists
            potential_url = potential_url.strip()

            # remove www from link
            potential_url = potential_url.replace("www.","")

            # parse url
            parsed_url = urlparse(potential_url)

            # if url is relative link, transform to absolute
            if (bool(parsed_url.netloc) == False):
                parsed_url = urlparse(urljoin(current_url, parsed_url.geturl()))

                with open(output_log_filename, 'a') as output_log:
                    output_log.write(f"status: relative URL resolved to absolute: {parsed_url}\n")

            with open(output_log_filename, 'a') as output_log:
                output_log.write(f"======{potential_url}======\nsource page: {current_url}\n")
            LOGGER.info(f"======{potential_url}======\nsource page: {current_url}")

            # remove internal reference if it exists, remove trailing forward slash if it exists
            parsed_url = parsed_url._replace(fragment="")
            parsed_url = urlparse(parsed_url.geturl().rstrip('/'))
            
            # make all links have https protocol
            parsed_url = parsed_url._replace(scheme="https")

            with open(output_log_filename, 'a') as output_log:
                output_log.write(f"after link normalization: {parsed_url.geturl()}\n")
            # LOGGER.info(f"after link normalization: {parsed_url.geturl()}")

            # if L has already been identified, continue loop
            if (parsed_url.geturl() in identified_links):
                with open(output_log_filename, 'a') as output_log:
                    output_log.write("status: ALREADY IDENTIFIED\n")
                # LOGGER.info("status: ALREADY IDENTIFIED\n")
                # LOGGER.info(f"url frontier status: {url_frontier}\n")
                continue
            
            # if L does not pass URL filter, continue loop
            # check if within domain
            within_domain = False
            for domain in acceptable_domains:
                if (domain == parsed_url.netloc):
                    within_domain = True
                    break

            if not within_domain:
                with open(output_log_filename, 'a') as output_log:
                    output_log.write(f"status: OUTSIDE OF ACCEPTABLE DOMAIN(S); netloc: {parsed_url.netloc}\n")
                # LOGGER.info("status: OUTSIDE OF ACCEPTABLE DOMAIN(S)\n")
                # LOGGER.info(f"url frontier status: {url_frontier}\n")
                continue

            # make request
            try:
                r = requests.head(parsed_url.geturl(), headers=headers)
            except:
                with open(output_log_filename, 'a') as output_log:
                    output_log.write("Request not successful.\n")
                # LOGGER.info(f"Request not successful.")
                # LOGGER.info(f"url frontier status: {url_frontier}\n")
                continue

            with open(output_log_filename, 'a') as output_log:
                output_log.write(f"Request made successfully, with request code {r.status_code}\n")
            # LOGGER.info(f"Request made successfully, with request code {r.status_code}\n")

            url_path = parsed_url.path
            potential_doc_name = os.path.split(url_path)[1]
            with open(output_log_filename, 'a') as output_log:
                output_log.write(f"Potential doc name: {potential_doc_name} from {os.path.split(url_path)}\n")

            # if doc matches a doc in input list, assign value to the page the url was found on (parsed url)
            if potential_doc_name in files_to_be_found.keys():
                # add parent page to list of pages where doc is linked from on site
                files_to_be_found[potential_doc_name].add(current_url)
                with open(output_log_filename, 'a') as output_log:
                    output_log.write(f"**DOC MATCH! Doc {potential_doc_name} found on page {current_url}\n")
                    output_log.write(f"{files_to_be_found}\n")
                # LOGGER.info(f"**DOC MATCH! Doc {potential_doc_name} found on page {current_url}\n")
                # LOGGER.info(f"{files_to_be_found}\n")
            # check if HTML (new potential link)
            elif "text/html" in r.headers["content-type"]:
                # add to identified links list + url frontier
                with open(output_log_filename, 'a') as output_log:
                    output_log.write("status: PASSED CHECKS. ADDED TO URL FRONTIER\n")
                # LOGGER.info("status: PASSED CHECKS. ADDED TO URL FRONTIER\n")
                identified_links.add(parsed_url.geturl())
                url_frontier.append(parsed_url.geturl())

    LOGGER.info("All links crawled. Starting output file creation...\n")

    # create output file and write data to it (document, page on site that contains link to doc)
    output_filename = "document_sources.output"
    with open(output_filename, "w") as crawler_outfile:
        LOGGER.info("Opened output file. Writing...\n")
        # key: doc name
        # val: list of parent pages that link to doc
        for key, val in files_to_be_found.items():
            if len(val) == 0:
                crawler_outfile.write(f"{key} ORPHAN-LINK\n")
            else:
                crawler_outfile.write(f"{key}")
                for parent_page in val:
                    crawler_outfile.write(f" {parent_page}")
                crawler_outfile.write("\n")

    return


if __name__ == "__main__":
    main()