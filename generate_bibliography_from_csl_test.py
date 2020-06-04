# This script uses several tools to create a bibliography from an existing .csl file
# Might be useful for future development
from dotenv import load_dotenv
load_dotenv()

import os
from pyzotero import zotero
import bibtexparser


import json

from citeproc import CitationStylesStyle, CitationStylesBibliography
from citeproc import Citation, CitationItem
from citeproc import formatter
from citeproc.source.json import CiteProcJSON
from citeproc.source.bibtex import BibTeX

print('\n'*100)

# Get all items in the ISAW Zotero
library_id = os.getenv('LIBRARY_ID')
library_type = os.getenv('LIBRARY_TYPE')
api_key = os.getenv('API_KEY')

z = zotero.Zotero(library_id, library_type, api_key)
# vItems = z.everything(z.top(sort="dateModified"))
# vItems = z.top(sort="dateModified", limit=10)
bibTeX = z.top(sort="dateModified", limit=10, format='bibtex')

# Save it and reopen it, because the documentation doesn't describe a way to load a string
with open('bibtex.bib', 'w') as bibtex_file:
    bibtexparser.dump(bibTeX, bibtex_file)
bib_source = BibTeX('bibtex.bib', encoding='utf-8')


# load a CSL style
fCSL = open('static/csl/mla-isawbib-full.csl', "rb")
fCSL = open('static/csl/mla-isawbib-authorless.csl', "rb")
bib_style = CitationStylesStyle(fCSL, validate=False)

# Create the citeproc-py bibliography, passing it the:
# * CitationStylesStyle,
# * BibliographySource (CiteProcJSON in this case), and
# * a formatter (plain, html, or you can write a custom formatter)

bibliography = CitationStylesBibliography(bib_style, bib_source, formatter.html)


# Processing citations in a document needs to be done in two passes as for some
# CSL styles, a citation can depend on the order of citations in the
# bibliography and thus on citations following the current one.
# For this reason, we first need to register all citations with the
# CitationStylesBibliography.
for item in bibTeX.entries:
    print(item['ID'])
    citation = Citation([CitationItem(item['ID'])])
    bibliography.register(citation)

print('')
print('Bibliography')
print('------------')

for item in bibliography.bibliography():
    print(str(item))














