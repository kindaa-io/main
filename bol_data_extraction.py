import re

# Retrieve inputs from Make.com scenario
raw_text = input.get('raw_text', '')
file_name = input.get('file_name', '')

# Clean up initial garbage header text if present
cleaned_raw_text = re.sub(r'^vessel_name[^\n\r]*', '', raw_text, flags=re.IGNORECASE).strip()

# 1. Extract BL Number (e.g., GSHA25010650, NBO26090478, SZ260903441)
# Prefix length varies by carrier/agent (2 letters "SZ", 3 "NBO", 4 "GSHA"/"TWSE").
# A bare 2-letter minimum is too permissive to just blind-scan the whole document
# with: it also matches 2-letter container references ("FX49162325") and VAT/country
# codes ("GB123456789"), and some carriers (Toptrans) put the "BILL OF LADING NO."
# label at the very end of the document, after all the container/cargo text -- so
# those false candidates can legitimately appear *before* the real number. Anchor
# the search to right after the B/L label itself (skipping over anything in between,
# like an intervening company name line) rather than scanning from the top; only
# fall back to a blind whole-document scan if no such label is found at all.
bl_label_match = re.search(r'\bB\s*/\s*L\.?\s*No\.?\s*:?\s*|\bBill\s+of\s+Lading\s*No\.?\s*:?\s*', cleaned_raw_text, re.IGNORECASE)

bl_number = None
if bl_label_match:
    bl_match = re.search(r'\b[A-Z]{2,4}\d{8,9}[A-Z]?\b', cleaned_raw_text[bl_label_match.end():])
    if bl_match:
        bl_number = bl_match.group(0)

if not bl_number:
    bl_match = re.search(r'\b[A-Z]{2,4}\d{8,9}[A-Z]?\b', cleaned_raw_text)
    bl_number = bl_match.group(0) if bl_match else None

# 2. Extract Voyage Number (Includes zero-padded and concatenated codes like 048W, GT611W, V.048W)
voyage_number = None

# Search for the literal "V." marker FIRST, across the whole document, before even
# trying the "Voy" label. The dot after "V" must be required (not optional):
# otherwise this matches the first word starting with "V" anywhere in the document
# (e.g. "VAT" in "VAT NO."), short-circuiting before it ever reaches the real
# "V.048W" voyage code. No leading \b on "V.": vessel name and voyage code are
# sometimes concatenated with no separator (e.g. "MSC IVAV.GT611W" = vessel
# "MSC IVA" + "V.GT611W"), so the "V" of the voyage marker can sit right against a
# preceding letter.
voyage_match = re.search(r'V\.\s*([A-Z0-9]{2,10})\b', cleaned_raw_text, re.IGNORECASE)

if voyage_match:
    cand = voyage_match.group(1).strip()
    if re.search(r'\d{2,}', cand) and cand != bl_number and 'VOY' not in cand.upper():
        voyage_number = cand

if not voyage_number:
    # Fall back to a "Voy"-label search only if no literal "V." marker was found (or
    # it didn't yield a usable code). Trying this in the same regex as "V." above
    # (as one alternation) is unsafe: re.search returns whichever alternative starts
    # earliest in the text, even if it's the worse capture. E.g. "...Ocean Vessel
    # Voy.No MSC AUDREY V.QX638W..." -- "Voy.No" appears before "V.QX638W", and once
    # "No" is absorbed by the "(?:No\.?)?" group, the capture grabs "MSC" (the start
    # of the vessel name) instead of the real code, which sits two lines later.
    # Trying "V." first across the whole document avoids that; this label-based
    # search is now just a secondary path for the rarer case where no "V.XXXX"
    # marker exists anywhere.
    voyage_match2 = re.search(
        r'\bVoy(?:age)?\.?\s*(?:No\.?)?\s*-?\s*:?\s*([A-Z0-9]{2,10})\b',
        cleaned_raw_text,
        re.IGNORECASE
    )
    if voyage_match2:
        cand = voyage_match2.group(1).strip()
        if re.search(r'\d{2,}', cand) and cand != bl_number and 'VOY' not in cand.upper():
            voyage_number = cand

has_vessel_context = re.search(r'\bvessel\b|\bvoy', cleaned_raw_text, re.IGNORECASE)

if not voyage_number and has_vessel_context:
    # Only look for a fallback voyage code in documents that actually mention a
    # vessel/voyage at all. Without this gate the fallback pattern (digits +
    # 1-2 trailing letters) also matches unrelated dimension/measurement text
    # like "H37CM" or "T47CM" in a plain packing list, producing a fake voyage
    # number for a document that isn't even a bill of lading.
    #
    # Prefix is letters only (e.g. "GT" in "GT611W"), not [A-Z0-9]*: an unbounded
    # alnum prefix lets this match deep inside long all-digit numbers (VAT numbers,
    # container/HS-code digit runs) by treating their leading digits as "prefix",
    # producing false positives when no real voyage code is present in the text.
    fallback_match = re.findall(r'\b[A-Z]{0,4}\d{2,4}[A-Z]{1,2}\b', cleaned_raw_text)
    for cand in fallback_match:
        if cand != bl_number and not cand.startswith(('BW', 'BS', 'GX', 'RAS', 'SFS')):
            voyage_number = cand
            break

# 3. Extract Vessel Name
vessel_name = None

# Strip this fixed carrier-boilerplate phrase before searching: it always contains
# the word "Vessel" itself (e.g. "...Stamp and Signature Laden on Board the Vessel
# Vessel MSC REEF Port of loading SHANGHAI..."), and since it's the *first* "Vessel"
# occurrence in the document, the search below would otherwise anchor on it instead
# of the real "Vessel" label that immediately precedes the actual ship name.
vessel_search_text = re.sub(r'Laden\s+on\s+Board\s+the\s+Vessel\s*', '', cleaned_raw_text, flags=re.IGNORECASE)

# Some carriers label this field "Vessel and Voyage No." (e.g. "VESSEL AND VOYAGE
# NO. MSC AUDREY / QX638W"), and OCR sometimes fuses the first two words into
# "VESSELAND" with no space at all. \bVessel\b can't match inside "VESSELAND" --
# there's no word/non-word boundary between "Vessel" and "and" when they're
# jammed together -- so normalize that back to two words before searching.
vessel_search_text = re.sub(r'\bVesselAnd\b', 'Vessel And', vessel_search_text, flags=re.IGNORECASE)

# Require what follows the label to look like actual label content (an uppercase
# letter or digit -- ship names and adjacent labels like "Voy-No." are always
# capitalized in these flattened forms), not lowercase prose. This catches generic
# mid-sentence uses of the word "vessel" in boilerplate/legal text (e.g. "...if the
# vessel operator delays...", "...loss of or damage to the vessel's cargo...") that
# the "Laden on Board the Vessel" strip above doesn't cover. The (?-i:...) forces
# case-sensitive matching for just this check despite the overall IGNORECASE flag.
# "/" is included alongside whitespace/colon as a separator: some labels are
# written "Ocean Vessel/Voy.No." with a slash joining the two label words.
vessel_matches = re.finditer(
    r'\b(?:Ocean\s+vessel|Vessel)\b(?=[\s\r\n:/]*(?:(?-i:[A-Z0-9])|$))[\s\r\n:/]*(.*)',
    vessel_search_text,
    re.IGNORECASE | re.DOTALL
)

for match in vessel_matches:
    following_text = match.group(1)
    lines = [line.strip() for line in following_text.splitlines() if line.strip()]

    for line in lines:
        if re.search(r'^(?:Date|Shipper|Consignee|Laden|PO:|Marks|Gross|Description|Port of Discharge|Place of)', line, re.IGNORECASE):
            break

        cleaned_line = line

        # Strip structural header labels attached to line start or inline. "And Vo[vy](age)?
        # No." handles the "Vessel And Voyage No. <value>" label (see the VesselAnd
        # normalization above) where "Vessel" alone doesn't account for the rest of it.
        # "Vo[vy]" (not just "Voy"): tolerates the common OCR misread of "Voy-No." as
        # "Vov-No." ("y" and "v" look alike in some scanned fonts).
        cleaned_line = re.sub(r'^(?:Vo[vy]-No\.?|Vo[vy]\.?\s*No\.?|And\s+Vo[vy](?:age)?\.?\s*No\.?|Ocean\s+Vessel|Vessel|Port\s+of\s+loading)\s*:?\s*', '', cleaned_line, flags=re.IGNORECASE).strip()
        # Anchored to the start only (no leading ".*?"): some BOLs stack labels
        # with no value in between ("Vessel Voy-No. Port of loading LUDWIGSHAFEN
        # EXPRESS..."), where this correctly skips the "Port of loading" label
        # that comes right after "Voy-No.". Others put the vessel value directly
        # after "Vessel" and only mention "Port of loading" later, as the *next*
        # field's label ("Vessel MSC REEF Port of loading SHANGHAI..."); a
        # search-and-strip (rather than start-anchored) would incorrectly eat
        # that real vessel name too, since there is no value between it and the
        # first "Port of loading" it can find.
        cleaned_line = re.sub(r'^Port\s+of\s+loading\s*', '', cleaned_line, flags=re.IGNORECASE).strip()

        # Handle voyage codes concatenated or spaced at the end (e.g., "LUDWIGSHAFEN EXPRESS V.048W" -> "LUDWIGSHAFEN EXPRESS",
        # or fully concatenated "MSC IVAV.GT611W" -> "MSC IVA"). The dot after "V" must be
        # required here too, otherwise this truncates at the first stray "V" inside the
        # vessel name itself (e.g. cutting "MSC IVA" down to "MSC I").
        cleaned_line = re.sub(r'\s*V\.\s*[A-Z0-9]+.*$', '', cleaned_line, flags=re.IGNORECASE).strip()

        # Handle a slash-separated voyage code with no "V." marker at all (e.g.
        # "MSC AUDREY / QX638W" -> "MSC AUDREY"), seen under the "Vessel And Voyage
        # No." label. Requires a digit in what follows the slash so a vessel name
        # that happens to contain a slash isn't truncated on nothing.
        cleaned_line = re.sub(r'\s*/\s*[A-Z0-9]*\d[A-Z0-9]*\b.*$', '', cleaned_line, flags=re.IGNORECASE).strip()

        # Cut off at the *next* field's "Port of loading" label, for the layout where
        # the vessel value sits directly after "Vessel" with no voyage code attached
        # (e.g. "Vessel MSC REEF Port of loading SHANGHAI..." -> "MSC REEF"). Safe to
        # apply unconditionally here: any leading "Port of loading" label was already
        # stripped above, so a remaining occurrence can only be this later field.
        cleaned_line = re.sub(r'\s*Port\s+of\s+loading\b.*$', '', cleaned_line, flags=re.IGNORECASE).strip()

        # Handle a voyage code with no separator at all, just a space (e.g. "MSC AUDREY
        # QX638W" -> "MSC AUDREY", seen under an "Ocean Vessel/Voy.No." stacked label).
        # Matches on shape -- letters+digits+letters, unlike a plain word such as
        # "AUDREY" or "EXPRESS" -- so a genuinely multi-word vessel name is untouched.
        cleaned_line = re.sub(r'\s+[A-Z]{1,4}\d{2,4}[A-Z]{0,2}\b\s*$', '', cleaned_line, flags=re.IGNORECASE).strip()

        # Remove explicit port destinations attached at the end
        cleaned_line = re.sub(r'\s+(?:SHANGHAI|NINGBO|ASHDOD|QINGDAO|XIAMEN|SHEADOU)(?:,CHINA|,ISRAEL)?$', '', cleaned_line, flags=re.IGNORECASE).strip()

        # Ignore standalone keywords (Vo[vy]-No.: tolerates the "Voy"/"Vov" OCR misread, see above)
        if cleaned_line and not re.match(r'^(?:Ocean\s+vessel|Vessel|Port\s+of\s+loading|Vo[vy]-No\.?)$', cleaned_line, re.IGNORECASE):
            vessel_name = cleaned_line
            break

    if vessel_name:
        break

# 4. Extract Order Codes
order_codes = []

if file_name:
    tokens = re.split(r'[\s,_\-]+', file_name)
    current_prefix = ""

    for token in tokens:
        sub_parts = token.split('/') if '/' in token else [token]

        for part in sub_parts:
            part = part.strip()
            if not part:
                continue

            # Order numbers are taken without the "." and anything after it, whether that's
            # a numeric sub-item ("BW234.43" -> "BW234") or garbage OCR trailing text
            # ("BW234.ASDDSF" -> "BW234") -- only the part before the first dot is kept.
            base = part.split('.', 1)[0]
            if not base:
                continue

            prefix_match = re.match(r'^([A-Z]{2,})(\d{2,})$', base, re.IGNORECASE)
            bare_num_match = re.match(r'^\d{2,}$', base)
            # A prefix can also appear as its own standalone token (e.g. "... RAS 344 65.6 ...",
            # where "RAS" sets the prefix for the bare numbers that follow it), not just fused
            # to the first number like "BW234". Without this branch such a token is silently
            # dropped and later bare numbers keep inheriting the previous prefix.
            bare_prefix_match = re.match(r'^[A-Z]{2,}$', base, re.IGNORECASE)

            if prefix_match:
                current_prefix = prefix_match.group(1).upper()
                order_codes.append(base.upper())
            elif bare_num_match and current_prefix:
                order_codes.append(f"{current_prefix}{base}")
            elif bare_prefix_match:
                current_prefix = base.upper()

unique_order_codes = list(dict.fromkeys(order_codes))

# Return values to Make.com scenario
return {
    'bl_number': bl_number,
    'vessel_name': vessel_name,
    'voyage_number': voyage_number,
    'order_codes': unique_order_codes
}
