from mediawiki import MediaWiki
from dotenv import load_dotenv
import os
import mediawiki
import urllib3
import json
import requests  # Import requests for session management

load_dotenv()

wiki = MediaWiki(url='https://atl.wiki/api.php')
wiki.login('WikiBot', os.getenv('BOT_PASSWORD'))

# Fetch all page titles
titles = wiki.allpages(results=10000)

# Initialize a list to hold the formatted page data
all_pages = []

# Iterate over each title
for title in titles:
    # Fetch the page object for each title
    try:
        page = wiki.page(title, auto_suggest=False, redirect=False)
    except mediawiki.exceptions.RedirectError:
        print(f'Skipping {title} because it is a redirect')
        continue
    
    # Now you can safely access the 'title' and 'categories' properties
    categories = page.categories

    # if the page has the category "Bot: Ignore" then skip it
    if 'Bot: Ignore' in categories:
        print(f'Skipping {title} because it has the category "Bot: Ignore"')
        continue

    print(f'Fetching {title} with categories {categories}')
    # Append the formatted data to the list
    all_pages.append([title, categories])

print(all_pages)

# put each unique category in a list
unique_categories = []
for page in all_pages:
    for category in page[1]:
        if category not in unique_categories:
            unique_categories.append(category)

# sort by name
unique_categories.sort()

# split into a list for each category of which pages are in it
# in the format [category, [page1, page2, ...]]
# a page can be in multiple categories
category_pages = []
for category in unique_categories:
    pages = []
    for page in all_pages:
        if category in page[1]:
            pages.append(page[0])
    category_pages.append([category, pages])

# get pages not in any category and put them in a new misc category
misc_pages = []
for page in all_pages:
    if not page[1]:
        misc_pages.append(page[0])
category_pages.append(['Misc', misc_pages])

print(category_pages)

# convert to a string in this style:
"""
=== some category ===
* [[page1]]
* [[page2]]

=== another category ===
* [[page3]]
* [[page4]]

=== Misc ===
* [[page5]]
* [[page6]]
"""

output = ''
for category in category_pages:
    output += f'\n== {category[0]} ==\n'
    for page in category[1]:
        output += f'* [[{page}]]\n'

print(output)

# find the page "Main Page" and find the text "<!-- beginwikibot -->" and put the output after that
main_page = wiki.page('Main Page')
main_text = main_page.wikitext
# replace everything between <!-- beginwikibot --> and <!-- endwikibot --> with blank (keeping the tags)
beginwikibot = '<!-- beginwikibot -->'
endwikibot = '<!-- endwikibot -->'
main_text = main_text[:main_text.find(beginwikibot) + len(beginwikibot)] + main_text[main_text.find(endwikibot):]
# add the output
output = f'{beginwikibot}\n{output}'
main_text = main_text.replace(beginwikibot, output)
print(main_text)

def edit_wikipedia_page(username, password, page_to_edit, new_content):
    # Initialize a session
    S = requests.Session()
    
    URL = "https://atl.wiki/api.php"
    
    # Step 1: GET Request to fetch login token
    PARAMS_0 = {
        "action": "query",
        "meta": "tokens",
        "type": "login",
        "format": "json"
    }
    
    R = S.get(url=URL, params=PARAMS_0)
    DATA = R.json()
    
    LOGIN_TOKEN = DATA['query']['tokens']['logintoken']
    
    # Step 2: POST Request to log in
    PARAMS_1 = {
        "action": "login",
        "lgname": username,
        "lgpassword": password,
        "lgtoken": LOGIN_TOKEN,
        "format": "json"
    }
    
    R = S.post(URL, data=PARAMS_1)
    
    # Step 3: GET request to fetch CSRF token
    PARAMS_2 = {
        "action": "query",
        "meta": "tokens",
        "format": "json"
    }
    
    R = S.get(url=URL, params=PARAMS_2)
    DATA = R.json()
    
    CSRF_TOKEN = DATA['query']['tokens']['csrftoken']
    
    # Step 4: POST request to edit a page
    PARAMS_3 = {
        "action": "edit",
        "title": page_to_edit,
        "token": CSRF_TOKEN,
        "format": "json",
        "text": new_content,
        "summary": "WikiBot: update directory"
    }
    
    R = S.post(URL, data=PARAMS_3)
    DATA = R.json()
    
    print(DATA)

edit_wikipedia_page('WikiBot', os.getenv('BOT_PASSWORD'), 'Main Page', main_text)