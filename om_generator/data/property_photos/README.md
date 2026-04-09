# Property Photos

Drop broker-provided property photos here before generating the OM.

## Directory structure
Create a subdirectory named after the property address (slugified):
  property_photos/<slug>/

Slug format: lowercase address, non-alphanumeric chars → hyphens,
consecutive hyphens collapsed, leading/trailing hyphens stripped.

Example:
  "9333 Clocktower Place, Fairfax VA 22031"
  → 9333-clocktower-place-fairfax-va-22031/

## File naming
Name photos 01 through 04 with .jpg, .jpeg, .png, or .webp extension:
  01.jpg  ← hero slot (leftmost, largest panel)
  02.jpg
  03.jpg
  04.jpg

Fewer than 4 photos is fine — empty slots fall back to Street View
or show a placeholder.
