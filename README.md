# Description

This is a web crawler designed to crawl UMich Rackham's site.
Given a list of document names, the crawler will return whether or not the document is linked on the site and its source page.

# Usage
```
% python3 crawler.py seedURL.txt input-documents.txt
```


`<seedURL.txt>` - a txt document that contains acceptable domain(s) to crawl, each separated by a newline


`<input-documents.txt>` - a txt document that contains names of documents to find, each separated by a newline
> Note: if the document name contains spaces, DO NOT use %20 in place of a space - simply include the space in the doc name


# Language(s) Used

- Python



Written by Rachel Cheng, Jun 2023.
