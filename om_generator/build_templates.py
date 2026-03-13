#!/usr/bin/env python3
"""
One-time build script: extracts sections from v3 prototype and creates Jinja2 templates.
Run once, then delete. The actual generator is generate_om.py.
"""
import re
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
V3_PATH = os.path.join(BASE_DIR, '..', 'investigation', 'newco_om_v3_regents_park.html')

with open(V3_PATH, 'r') as f:
    v3 = f.read()
    v3_lines = v3.split('\n')

# Extract logo base64
logo_match = re.search(r'(data:image/png;base64,[A-Za-z0-9+/=]+)', v3_lines[296])
LOGO_B64 = logo_match.group(1) if logo_match else ''

# Extract CSS (lines 9-186, content between <style> tags)
css_lines = v3_lines[8:187]
css_content = '\n'.join(css_lines).replace('<style>', '').replace('</style>', '').strip()

def get_section(start, end):
    """Get lines start-end (1-indexed inclusive)"""
    return '\n'.join(v3_lines[start-1:end])


# ============================
# Write base.html
# ============================
base_html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Offering Memorandum — {{{{ property_name }}}} — v3</title>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500&family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;1,400&display=swap" rel="stylesheet">
<style>
{css_content}
</style>
</head>
<body>

{{% include "sections/cover.html" %}}

{{% include "sections/executive_summary.html" %}}

{{% include "sections/financials.html" %}}

{{% include "sections/development_intelligence.html" %}}

{{% include "sections/market_overview.html" %}}

{{% include "sections/location_analysis.html" %}}

</body>
</html>
'''

os.makedirs(os.path.join(BASE_DIR, 'templates', 'sections'), exist_ok=True)
with open(os.path.join(BASE_DIR, 'templates', 'base.html'), 'w') as f:
    f.write(base_html)
print(f"base.html: {len(base_html)} chars")

print(f"\nLogo base64: {len(LOGO_B64)} chars — stored as {{{{ wo_logo_base64 }}}} variable")
print("Build script complete. Now create section templates manually with Jinja2 variables.")
