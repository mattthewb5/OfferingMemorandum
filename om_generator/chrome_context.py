"""Chrome-context builder.

Page-infrastructure constants — section names and page numbers shown in
each page's footer. These never vary per property, so they live in their
own builder rather than the per-property seed context.

Index 0 is unused (the cover has a custom footer). Indices 1–6 map to:
  1: Executive Summary
  2: Financial Analysis
  3: Development Intelligence
  4: Market Overview
  5: Location Analysis
  6: Contact & Next Steps
"""

_FOOTER_SECTION_NAMES = (
    "",
    "Executive Summary",
    "Financial Analysis",
    "Development Intelligence",
    "Market Overview",
    "Location Analysis",
    "Contact & Next Steps",
)

_PAGE_NUMBERS = ("", "2", "3", "4", "5", "6", "7")


def build_chrome_context() -> dict:
    """Return the static chrome dict consumed by section page-footers."""
    return {
        "footer_section_names": list(_FOOTER_SECTION_NAMES),
        "page_numbers": list(_PAGE_NUMBERS),
    }
