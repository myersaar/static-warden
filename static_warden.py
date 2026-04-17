#!/usr/bin/env python3
"""
Bitwarden JSON Export -> Searchable HTML Page

Usage:
  python bitwarden_json_to_searchable_html.py input.json output.html

Notes:
- Works with Bitwarden *unencrypted* JSON exports
- Generates a single self-contained HTML file (no external assets)
- Client-side search (nothing leaves the browser)
"""

import json
import sys
import html
from datetime import datetime

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Bitwarden Vault Export</title>
  <style>
    body {{ 
      font-family: Roboto, Helvetica, Arial, sans-serif; 
      margin: 0; 
      background-color: #f5f5f5; 
      color: rgba(0, 0, 0, 0.87);
    }}
    .app-bar {{
      background-color: #1976d2;
      color: white;
      padding: 1rem 2rem;
      box-shadow: 0px 2px 4px -1px rgba(0,0,0,0.2), 0px 4px 5px 0px rgba(0,0,0,0.14), 0px 1px 10px 0px rgba(0,0,0,0.12);
      display: flex;
      align-items: center;
      justify-content: space-between;
      position: sticky;
      top: 0;
      z-index: 1100;
    }}
    .app-bar h1 {{ margin: 0; font-size: 1.25rem; font-weight: 500; }}
    .container {{ max-width: 800px; margin: 2rem auto; padding: 0 1rem; }}
    .search-container {{
      margin-bottom: 2rem;
      position: relative;
    }}
    input {{ 
      width: 100%; 
      padding: 12px 16px; 
      font-size: 1rem; 
      border: 1px solid rgba(0, 0, 0, 0.23);
      border-radius: 4px;
      background: white;
      box-sizing: border-box;
      transition: border-color 200ms cubic-bezier(0.4, 0, 0.2, 1) 0ms, box-shadow 200ms cubic-bezier(0.4, 0, 0.2, 1) 0ms;
    }}
    input:focus {{
      outline: none;
      border-color: #1976d2;
      border-width: 2px;
      padding: 11px 15px;
    }}
    .meta {{ color: rgba(0, 0, 0, 0.6); font-size: 0.875rem; margin-top: 0.5rem; text-align: right; }}
    .item {{ 
      background: white; 
      border-radius: 4px; 
      padding: 16px; 
      margin-bottom: 16px; 
      box-shadow: 0px 2px 1px -1px rgba(0,0,0,0.2), 0px 1px 1px 0px rgba(0,0,0,0.14), 0px 1px 3px 0px rgba(0,0,0,0.12);
      content-visibility: auto;
      contain-intrinsic-size: 120px;
    }}
    .title {{ 
      font-size: 1.25rem; 
      font-weight: 500; 
      margin-bottom: 8px;
      color: rgba(0, 0, 0, 0.87);
    }}
    .field {{ 
      margin-top: 8px; 
      display: flex;
      flex-direction: column;
    }}
    .label {{ 
      font-size: 0.75rem; 
      color: rgba(0, 0, 0, 0.6); 
      font-weight: 400;
      text-transform: uppercase;
      letter-spacing: 0.08333em;
    }}
    .value {{ 
      font-family: 'Roboto Mono', monospace; 
      font-size: 0.875rem;
      word-break: break-all;
      background: #f8f8f8;
      padding: 4px 8px;
      border-radius: 4px;
      margin-top: 2px;
    }}
  </style>
</head>
<body>

<div class="app-bar">
  <h1>Bitwarden Vault</h1>
  <div style="font-size: 0.8rem; opacity: 0.8;">Generated {generated}</div>
</div>

<div class="container">
  <div class="search-container">
    <input id="search" placeholder="Search name, username, URI, notes…" autofocus />
  </div>

  <div id="items"></div>
</div>

<script>
const DATA = {data};

const container = document.getElementById('items');
const search = document.getElementById('search');

let visibleCount = 100;

function render(items) {{
  container.innerHTML = '';
  const fragment = document.createDocumentFragment();
  const slice = items.slice(0, visibleCount);

  slice.forEach(item => {{
    const div = document.createElement('div');
    div.className = 'item';

    div.innerHTML = `
      <div class="title">${{item.name}}</div>
      ${{item.username ? `<div class="field"><span class="label">Username:</span> <span class="value">${{item.username}}</span></div>` : ''}}
      ${{item.password ? `<div class="field"><span class="label">Password:</span> <span class="value">${{item.password}}</span></div>` : ''}}
      ${{item.uris.length ? `<div class="field"><span class="label">URIs:</span> <span class="value">${{item.uris.join('<br>')}}</span></div>` : ''}}
      ${{item.notes ? `<div class="field"><span class="label">Notes:</span> <span class="value">${{item.notes}}</span></div>` : ''}}
    `;

    fragment.appendChild(div);
  }});
  container.appendChild(fragment);
}}

let debounceTimer;
function filter() {{
  const q = search.value.toLowerCase().trim();
  const filtered = q ? DATA.filter(i => i.search.includes(q)) : DATA;
  render(filtered);
}}

search.addEventListener('input', () => {{
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(filter, 150);
}});

render(DATA);
</script>

</body>
</html>"""


def main():
    if len(sys.argv) != 3:
        print("Usage: python bitwarden_json_to_searchable_html.py input.json output.html")
        sys.exit(1)

    input_file, output_file = sys.argv[1], sys.argv[2]

    with open(input_file, 'r', encoding='utf-8') as f:
        bw = json.load(f)

    items = []

    for item in bw.get('items', []):
        login = item.get('login') or {}
        uris = [u.get('uri') for u in (login.get('uris') or []) if u.get('uri')]

        record = {
            'name': html.escape(item.get('name', '')),
            'username': html.escape(login.get('username', '')) if login.get('username') else '',
            'password': html.escape(login.get('password', '')) if login.get('password') else '',
            'uris': [html.escape(u) for u in uris],
            'notes': html.escape(item.get('notes', '')) if item.get('notes') else '',
        }

        search_blob = ' '.join([
            record['name'],
            record['username'],
            record['notes'],
            ' '.join(record['uris'])
        ]).lower()

        record['search'] = search_blob
        items.append(record)

    html_out = TEMPLATE.format(
        generated=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        data=json.dumps(items)
    )

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_out)

    print(f"Wrote searchable vault to {output_file}")


if __name__ == '__main__':
    main()
