# This script will map FDA upload data to items in Roger's Zotero bibliography
from dotenv import load_dotenv
load_dotenv()

import os
from pyzotero import zotero


# Get all items in the ISAW Zotero
library_id = os.getenv('LIBRARY_ID')
library_type = os.getenv('LIBRARY_TYPE')
api_key = os.getenv('API_KEY')

z = zotero.Zotero(library_id, library_type, api_key)
vItems = z.everything(z.top(sort="dateModified"))

vItemTypes = []
for item in vItems:
    sItemType = item['data']['itemType']
    if not sItemType in vItemTypes:
        vItemTypes.append(sItemType)
        
print(vItemTypes)







