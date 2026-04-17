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
  <title>Static Warden</title>
  <style>
    body {{ font-family: system-ui, -apple-system, BlinkMacSystemFont, sans-serif; margin: 2rem; background: #fafafa; }}
    h1 {{ margin-bottom: 0.2rem; }}
    .meta {{ color: #666; margin-bottom: 1.5rem; }}
    input {{ width: 100%; padding: 0.6rem; font-size: 1rem; margin-bottom: 1rem; }}
    .item {{ background: white; border-radius: 8px; padding: 1rem; margin-bottom: 1rem; box-shadow: 0 1px 4px rgba(0,0,0,.08); }}
    .title {{ font-size: 1.1rem; font-weight: 600; }}
    .field {{ margin-top: 0.3rem; }}
    .label {{ font-weight: 500; color: #444; }}
    .value {{ font-family: monospace; white-space: pre-wrap; }}
    .hidden {{ display: none; }}
  </style>
</head>
<body>

<h1>Bitwarden Vault</h1>
<div class="meta">Generated {generated}</div>

<input id="search" placeholder="Search name, username, URI, notes…" autofocus />

<div id="items"></div>

<script>
const DATA = {data};

const container = document.getElementById('items');
const search = document.getElementById('search');

function render(items) {{
  container.innerHTML = '';
  items.forEach(item => {{
    const div = document.createElement('div');
    div.className = 'item';

    div.innerHTML = `
      <div class="title">${{item.name}}</div>
      ${{item.username ? `<div class="field"><span class="label">Username:</span> <span class="value">${{item.username}}</span></div>` : ''}}
      ${{item.password ? `<div class="field"><span class="label">Password:</span> <span class="value">${{item.password}}</span></div>` : ''}}
      ${{item.uris.length ? `<div class="field"><span class="label">URIs:</span> <span class="value">${{item.uris.join('<br>')}}</span></div>` : ''}}
      ${{item.notes ? `<div class="field"><span class="label">Notes:</span> <span class="value">${{item.notes}}</span></div>` : ''}}
    `;

    container.appendChild(div);
  }});
}}

function filter() {{
  const q = search.value.toLowerCase();
  const filtered = DATA.filter(i => i.search.includes(q));
  render(filtered);
}}

search.addEventListener('input', filter);
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
