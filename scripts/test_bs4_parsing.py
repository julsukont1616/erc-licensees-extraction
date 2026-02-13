from bs4 import BeautifulSoup

with open('debug_process_table.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

# Find tbody
tbody = soup.find('tbody')
print(f'Found tbody: {tbody is not None}')

if tbody:
    # Try different ways to find rows
    method1 = tbody.find_all('tr', id=True)
    print(f'Method 1 - find_all("tr", id=True): {len(method1)} rows')

    method2 = tbody.find_all('tr', class_=lambda x: 'rgRow' in str(x) if x else False)
    print(f'Method 2 - find_all with class lambda: {len(method2)} rows')

    method3 = tbody.find_all('tr')
    print(f'Method 3 - find_all("tr"): {len(method3)} rows')

    # Check the first tr in tbody
    if method3:
        first_tr = method3[0]
        print(f'\nFirst tr element:')
        print(f'  tag: {first_tr.name}')
        print(f'  has id: {first_tr.has_attr("id")}')
        print(f'  id value: {first_tr.get("id", "None")}')
        print(f'  class: {first_tr.get("class", "None")}')
        print(f'  HTML: {str(first_tr)[:200]}')
