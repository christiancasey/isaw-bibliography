from dotenv import load_dotenv
load_dotenv()

import os

import csv
import re

from flask import Flask, Markup, render_template, url_for
from pyzotero import zotero


from collections import Counter

from pprint import pprint

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])

library_id = os.getenv('LIBRARY_ID')
library_type = os.getenv('LIBRARY_TYPE')
api_key = os.getenv('API_KEY')

z = zotero.Zotero(library_id, library_type, api_key)
isawbib_json = z.everything(z.top(sort="dateModified"))



# Work with FDA-specific data for Bagnall works
# Need to speed up—cache data???
with open('data/2451-28115.csv') as f:
    reader = csv.reader(f)
    fda_data = {row[12]: row[8] for row in reader if row[12]}

for item in isawbib_json:
    item['fda_present'] = 0
    if item['data']['archive'] == 'https://archive.nyu.edu/handle/2451/28115':
        if item['data']['archiveLocation'] in fda_data.keys():
            item['links']['alternate']['href'] = fda_data[item['data']['archiveLocation']]
            item['fda_present'] = 1


# Add citations
cit = z.add_parameters(content='bib', style='https://raw.githubusercontent.com/diyclassics/isaw-bibliography/master/static/csl/mla-isawbib-author.csl', sort="dateModified")

isawbib_cit = z.everything(z.top())

# Helper function to reduce date info to four-digit year
def simplify_date(date_string):
    temp = date_string
    temp = ''.join([s for s in temp if s.isdigit()]) # Remove any non digits
    return (temp[:4]) # Limit to first four characters; sufficient? (What if there was numerical day/month/etc. info in field?)

# Helper function to format citations
def fix_citations_auth(cit):
    match = 'Bagnall, Roger S.'
    open = '<div class="csl-entry">'
    close = '</div>'

    cit = cit.replace(open,'').replace(close,'')

    # x = "Bagnall, Roger S.|J. F. Oates|W.H.Willis~“A Checklist of Editions of Greek Papyri and Ostraca”~Bulletin of the American Society of Papyrologists, vol. 11, 1974, pp. 1–35~https://archive.nyu.edu/handle/2451/28115, D13."
    author = cit.split('~')[0]
    bib = cit.split('~')[1:]

    authors = author.split('|')

    if match in authors:
        authors.remove(match)

    # print(authors)

    if len(authors) == 2:
        withs = " and ".join(authors)
        withs = ' (with '+withs+')'
    elif len(authors) > 2:
        withs = ", ".join(authors[:-1])+', and '+authors[-1]
        withs = ' (with '+withs+')'
    else:
        withs = ''

    bib = ". ".join(bib)

    # if auths.endswith('.'):
    #     bib = auths + ' ' + bib
    # else:
    #     bib = auths + '. ' + bib

    bib = open + bib + withs + close

    bib = bib.replace('https://archive.nyu.edu/handle/2451/28115,', 'NYU FDA Entry').replace('https://archive.nyu.edu/handle/2451/28115.', '')

    bib = re.sub(r'(https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:;%_\+.~#?&//=]*))', '<a href=\'\g<1>\'>\g<1></a>', bib)

    return bib

def fix_citations_main(cit):
    match = 'Bagnall, Roger S.'
    open = '<div class="csl-entry">'
    close = '</div>'

    cit = cit.replace(open,'').replace(close,'')

    # x = "Bagnall, Roger S.|J. F. Oates|W.H.Willis~“A Checklist of Editions of Greek Papyri and Ostraca”~Bulletin of the American Society of Papyrologists, vol. 11, 1974, pp. 1–35~https://archive.nyu.edu/handle/2451/28115, D13."
    author = cit.split('~')[0]
    bib = cit.split('~')[1:]

    authors = author.split('|')

    if len(authors) == 2:
        auths = " and ".join(authors)
    elif len(authors) > 2:
        auths = ", ".join(authors[:-1])+', and '+authors[-1]
    else:
        auths = author

    bib = ". ".join(bib)

    if auths.endswith('.'):
        bib = auths + ' ' + bib
    else:
        bib = auths + '. ' + bib

    bib = open + bib + close

    bib = bib.replace('https://archive.nyu.edu/handle/2451/28115,', 'NYU FDA Entry').replace('https://archive.nyu.edu/handle/2451/28115.', '')

    bib = re.sub(r'(https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:;%_\+.~#?&//=]*))', '<a href=\'\g<1>\'>\g<1></a>', bib)

    return bib

# More elegant way to write this?
for i, item in enumerate(isawbib_cit):
    isawbib_json[i]['data']['citation'] = fix_citations_main(item)
    isawbib_json[i]['data']['citation_auth'] = fix_citations_auth(item)

def _sort_zotero_date(zotero_items, reverse=True):
    return sorted(zotero_items, key=lambda k: k['data']['date'], reverse=reverse)

def get_zotero_data():
    z = zotero.Zotero(library_id, library_type, api_key)
    isawbib_json = z.everything(z.top(sort="dateModified"))
    # cit = z.add_parameters(content='bib', style='https://www.zotero.org/styles/transactions-of-the-american-philological-association', sort="dateModified")
    cit = z.add_parameters(content='bib', style='mla', sort="dateModified")
    isawbib_cit = z.everything(z.top())

    # More elegant way to write this?
    for i, item in enumerate(isawbib_cit):
        isawbib_json[i]['data']['citation'] = item
    items = isawbib_json
    count = len(items)
    items = _sort_zotero_date(items)
    return items, count


@app.route('/')
def homepage():
    items = isawbib_json
    count = len(items)
    items = _sort_zotero_date(items)
    for item in isawbib_json:
        item['data']['citation_'] = item['data']['citation']
    return render_template('isaw-bibliography.html', title=None, items=items, count=count)


@app.route('/refresh')
# Fix refresh to use FDA scripts
def refresh():
	items, count = get_zotero_data()
	count = len(items)
	items = _sort_zotero_date(items)
	return render_template('isaw-bibliography.html', title=None, items=items, count=count)


@app.route('/year/<year>')
def bib_by_year(year):
    items = []
    for item in isawbib_json:
        if item['data']['date'] == year:
            items.append(item)
        item['data']['citation_'] = item['data']['citation']
    count = len(items)
    items = _sort_zotero_date(items)
    return render_template('isaw-bibliography.html', title='Year: %s' % str(year), items=items, count=count)


# Roger's custom view
class NumberedItem:
    def __init__(self,item_arg):
        self.item = item_arg
        
        self.iItemNumber = -1
        if len(self.item['data']['archiveLocation'][1:]) > 0:
            sItemNumber = self.item['data']['archiveLocation'][1:]
            sItemNumber = re.sub(r'\D','',sItemNumber)
            self.iItemNumber = int(sItemNumber)
            
        self.item['data']['itemNumber'] = self.iItemNumber
        
    def __lt__(self,other):
        return(self.iItemNumber<other.iItemNumber)
        
def render_bagnall_template(items, count):
    
    categories = []
    with open('data/bagnall-codes.csv') as f:
        reader = csv.reader(f)
        # bagnall_codes = {row[0]: row[1] for row in reader}
        # items_by_category = {row[0]: [] for row in reader}
        for row in reader:
            item_list = {'code': row[0], 'description': row[1], 'items': []}
            categories.append(item_list)
        
    item_list = {'code': 'X', 'description': 'Uncategorized', 'items': []}
    categories.append(item_list)
    
    for item in items:
        
        bAdded = False # If adding an item to a category fails, dump it into catchall below
        
        # If they have an archiveLocation value, use it to find the category
        if len(item['data']['archiveLocation']) > 0:
            iCatIndex = [iCatIndex for iCatIndex, cat in enumerate(categories) if cat['code'] == item['data']['archiveLocation'][0]]
            if len(iCatIndex) > 0:
                bAdded = True
            else:
                print(item['data']['archiveLocation'])
            
            # if len(item['data']['archiveLocation']) > 0:
            #     sItemNumber = item['data']['archiveLocation'][1:]
            #     sItemNumber = re.sub(r'\D','',sItemNumber)
            #     iItemNumber = int(item['data']['archiveLocation'][1:])
            #     print(iItemNumber)
        
        if not bAdded:
            iCatIndex = [iCatIndex for iCatIndex, cat in enumerate(categories) if cat['code'] == 'X']
            
        categories[iCatIndex[0]]['items'].append(item)
        
    # Sort the items inside the categories using the NumberedItem object
    for i in range(len(categories)):
        
        print('%s %i' % (categories[i]['code'], len(categories[i]['items'])))
        
        if len(categories[i]['items']) > 0:
            numbered_items = [ NumberedItem(item) for item in categories[i]['items'] ]
            numbered_items.sort()
            categories[i]['items'] = [ ni.item for ni in numbered_items ]
            
        
    return render_template('isaw-bibliography-bagnall.html', title='Author: bagnall', items=items, categories=categories, count=count)


@app.route('/author/<author>')
@app.route('/authors/<author>')
def bib_by_author(author):
    items = []
    for item in isawbib_json:
        for creator in item['data']['creators']:
            for authors in creator.values():
                if author.lower() in authors.lower():
                    # Perhaps this will prevent the duplicates, see comment below
                    if item not in items:
                        items.append(item)
        
        item['data']['citation_'] = item['data']['citation_auth']
        if item['fda_present'] == 0:
            item['data']['citation_'] = re.sub(r'NYU FDA Entry .+?\.','',item['data']['citation_'])
        # Reduce dates to year only
        item['data']['date'] = simplify_date(item['data']['date'])

    # Remove duplicates—to do: why are there duplicates?
    #   Possible solution: See above in the creator loop, multiple author tags might cause duplicate appends
    # Cf. Method #2 https://www.geeksforgeeks.org/python-removing-duplicate-dicts-in-list/
    items = [i for n, i in enumerate(items) if i not in items[n + 1:]]
    
    count = len(items)
    items = _sort_zotero_date(items)
    # print([item['key'] for item in items])
    if author == 'bagnall':
        return render_bagnall_template(items, count)
    
    return render_template('isaw-bibliography.html', title='Author: %s' % author, items=items, count=count)


@app.route('/tag/<tag>')
@app.route('/tags/<tag>')
def bib_by_tag(tag):
    items = []
    for item in isawbib_json:
        for tags in item['data']['tags']:
            if tag in tags.values():
                items.append(item)
    count = len(items)
    items = _sort_zotero_date(items)
    return render_template('isaw-bibliography.html', title='Tag: %s' % tag, items=items, count=count)


@app.route('/author/<author>/chart')
@app.route('/authors/<author>/chart')
def chart(author):

    items = []
    for item in isawbib_json:
        for creator in item['data']['creators']:
            for authors in creator.values():
                if author.lower() in authors.lower():
                    items.append(item)

    year_count = Counter([int(item['data']['date']) for item in items if item['data']['date'].isnumeric()])

    # Fill in missing years
    min_key = min(year_count)
    max_key = max(year_count)
    year_count.update(dict.fromkeys(set(range(min_key, max_key+1)).difference(year_count), 0))

    year_count = sorted(year_count.most_common())
    labels, values = zip(*year_count)
    max_value = max(values)

    return render_template('isaw-bibliography-chart.html', author=author, values=values, labels=labels, max_value=max_value)

@app.route('/json')
def print_first_record():
    return render_template('isaw-json.html', item=isawbib_json[400])


if __name__ == '__main__':
    app.run()