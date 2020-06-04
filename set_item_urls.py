# This script will map FDA upload data to items in Roger's Zotero bibliography
from dotenv import load_dotenv
load_dotenv()

import os
import csv
from pyzotero import zotero


# Work with FDA-specific data for Bagnall works
# Need to speed up—cache data???
with open('data/2451-28115.csv') as f:
    reader = csv.reader(f)
    fda_data = {row[12]: row[8] for row in reader if row[12]}

# Get all items in the ISAW Zotero
library_id = os.getenv('LIBRARY_ID')
library_type = os.getenv('LIBRARY_TYPE')
api_key = os.getenv('API_KEY')

z = zotero.Zotero(library_id, library_type, api_key)
isawbib_json = z.everything(z.top(sort="dateModified"))

# Loop through items and update URL with FDA file
i = 0
for item in isawbib_json:
    
    # Determines that it's Roger's item perhaps? (Copied from Patrick's code)
    if item['data']['archive'] == 'https://archive.nyu.edu/handle/2451/28115':
        
        # If it is in the list of FDA uploads (according to Roger's codes)
        if item['data']['archiveLocation'] in fda_data.keys():
            
            # Make sure you don't overwrite anything right now
            if True: #item['data']['url'] == '':
                i+=1
                item['data']['url'] = fda_data[item['data']['archiveLocation']]
                print('%i: %s' %(i,item['data']['url']))
                z.update_item(item)



