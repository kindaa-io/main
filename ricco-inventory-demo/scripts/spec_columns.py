"""Column definitions from demo-spec.md §4, in spec order.

Each column: (id, title, type, phase, extra). `id` is the custom column id we set
(lowercase + underscore). Reflections are created by monday (two-way connects) and
are listed with type "reflection" so ordering/renaming can find them.

Colour mapping from spec names to monday StatusColumnColors (logged in BUILD-LOG):
grey=explosive, dark grey=american_gray, light blue=chili_blue, blue=bright_blue,
purple=purple, orange=working_orange, dark orange=dark_orange, light green=bright_green,
green=done_green, dark green=grass_green, yellow=egg_yolk, red=stuck_red.
"""

C = {"grey": "explosive", "dark grey": "american_gray", "light blue": "chili_blue",
     "blue": "bright_blue", "purple": "purple", "orange": "working_orange",
     "dark orange": "dark_orange", "light green": "bright_green", "green": "done_green",
     "dark green": "grass_green", "yellow": "egg_yolk", "red": "stuck_red"}


def status(*labels):
    """labels: (label, colour name[, done])"""
    return {"labels": [{"label": l[0], "color": C[l[1]] if l[1] in C else l[1], "index": i,
                        "is_done": bool(len(l) > 2 and l[2])} for i, l in enumerate(labels)]}


def dropdown(labels, single):
    d = {"labels": [{"label": l} for l in labels]}
    if single:
        d["limit_select"] = True
        d["label_limit_count"] = 1
    return d


USD = {"unit": {"symbol": "$", "direction": "left"}}
CATEGORIES = ["Sheet Goods", "Edgeband", "Hinges", "Slides & Hardware", "Accessories", "Finish / Paint"]

BOARDS = {
    "Suppliers": [
        ("contact_person", "Contact person", "text", 2, None),
        ("email", "Email", "email", 2, None),
        ("phone", "Phone", "phone", 2, None),
        ("payment_terms", "Payment terms", "text", 2, None),
        ("categories", "Categories supplied", "dropdown", 2, dropdown(CATEGORIES, single=False)),
        ("active", "Active", "status", 2, status(("Active", "green"), ("Inactive", "grey"))),
        (None, "Products", "reflection", 4, {"from": ("Materials Catalogue", "default_supplier")}),
        (None, "Purchase Orders", "reflection", 4, {"from": ("Purchase Orders", "supplier")}),
        ("total_ordered", "Total ordered", "mirror", 5, None),
        ("open_pos", "Open POs", "mirror", 5, None),
    ],
    "Materials Catalogue": [
        # Category colours are not in the spec; chosen for distinctness.
        ("category", "Category", "status", 2, status(("Sheet Goods", "dark_blue"), ("Edgeband", "sunset"),
                                                     ("Hinges", "teal"), ("Slides & Hardware", "berry"),
                                                     ("Accessories", "lavender"), ("Finish / Paint", "peach"))),
        ("stock_type", "Stock type", "status", 2, status(("Stocked", "green"), ("Order-to-project", "blue"))),
        ("uom", "UoM", "dropdown", 2, dropdown(["sheet", "ft", "each", "pair", "gallon", "box"], single=True)),
        ("pack_size", "Pack size", "numbers", 2, None),
        ("default_supplier", "Default supplier", "board_relation", 4, None),
        ("supplier_email", "Supplier email", "mirror", 5, None),
        ("supplier_part", "Supplier Part #", "text", 2, None),
        ("minimum_level", "Minimum level", "numbers", 2, None),
        ("last_price", "Last purchase price", "numbers", 2, USD),
        (None, "⚙️ Applied in", "reflection", 4, {"from": ("Stock Movements", "applied_in")}),
        (None, "⚙️ Applied out", "reflection", 4, {"from": ("Stock Movements", "applied_out")}),
        ("in_total", "⚙️ In total", "mirror", 5, None),
        ("out_total", "⚙️ Out total", "mirror", 5, None),
        ("on_hand", "On hand", "formula", 5, None),
        (None, "⚙️ Request lines", "reflection", 4, {"from": ("Request lines", "product")}),
        ("reserved", "Reserved", "mirror", 5, None),
        ("available", "Available", "formula", 5, None),
        ("stock_state", "Stock state", "formula", 5, None),
        ("stock_value", "Stock value", "formula", 5, None),
        ("notes", "Notes", "long_text", 2, None),
    ],
    "Material Requests": [
        ("request_no", "Request #", "auto_number", 2, None),
        ("status", "Status", "status", 2, status(
            ("Submitted", "light blue"), ("In Review", "blue"), ("Ordering", "purple"),
            ("Waiting for Delivery", "orange"), ("Ready for Production", "light green"),
            ("Issue Materials", "dark orange"), ("Issuing", "yellow"), ("Closed", "green", True),
            ("On Hold", "red"), ("Cancelled", "dark grey"))),
        ("materials_complete", "✅ Materials complete", "checkbox", 2, None),
        # Built by Omer in the UI (2026-10-28): two-way, single, -> Units + Projects. Replaces
        # the spec's "Unit / Project" (Phase 6) and "Production Calendar job" (deleted).
        ("board_relation_mm8j4n2b", "Project \\ Unit", "board_relation", 4, None),
        ("programmer", "Programmer", "people", 2, None),
        ("purchaser", "Purchaser", "people", 2, None),
        ("inventory_owner", "Inventory owner", "people", 2, None),
        ("needed_by", "Needed by", "date", 2, None),
        ("submitted_on", "Submitted on", "date", 2, None),
        ("source_file", "Source file", "file", 2, None),
        ("purchase_orders", "Purchase Orders", "board_relation", 4, None),
        ("po_status", "PO status", "mirror", 5, None),
        ("material_cost", "Material cost", "mirror", 5, None),
        ("notes", "Notes", "long_text", 2, None),
    ],
    "Request lines": [
        ("product", "Product", "board_relation", 4, None),
        ("qty_requested", "Qty requested", "numbers", 3, None),
        ("uom", "UoM", "mirror", 5, None),
        ("on_hand", "On hand", "mirror", 5, None),
        ("available", "Available", "mirror", 5, None),
        ("supplier", "Supplier", "mirror", 5, None),
        ("status", "Decision", "status", 3, status(
            ("Pending", "grey"), ("From Stock", "green"), ("Partial", "yellow"), ("To Order", "orange"),
            ("Ordered", "purple"), ("Received", "blue"), ("Issued", "dark green", True),
            ("Cancelled", "dark grey"))),
        ("qty_reserved", "Qty reserved", "numbers", 3, None),
        ("qty_to_order", "Qty to order", "numbers", 3, None),
        ("qty_outstanding", "Qty outstanding", "formula", 5, None),
        ("po_line", "PO line", "board_relation", 4, None),
        ("qty_ordered", "Qty ordered", "mirror", 5, None),
        ("qty_received", "Qty received", "mirror", 5, None),
        ("po_unit_price", "PO unit price", "mirror", 5, None),
        ("est_unit_price", "Est. unit price", "mirror", 5, None),
        ("qty_issued", "Qty issued", "numbers", 3, None),
        ("line_cost", "Line cost", "formula", 5, None),
    ],
    "Purchase Orders": [
        ("po_no", "PO #", "auto_number", 2, {"prefix": "PO-000", "scope": "board", "order": "ascending"}),
        ("status", "Status", "status", 2, status(
            ("Draft", "grey"), ("Approved", "blue"), ("Sent", "purple"), ("Partially Received", "orange"),
            ("Received", "green"), ("Closed", "dark green", True), ("Cancelled", "dark grey"))),
        ("supplier", "Supplier", "board_relation", 4, None),
        ("supplier_email", "Supplier email", "mirror", 5, None),
        ("contact", "Contact", "mirror", 5, None),
        ("projects", "Projects", "board_relation", 6, None),
        (None, "Material Requests", "reflection", 4, {"from": ("Material Requests", "purchase_orders")}),
        ("purchaser", "Purchaser", "people", 2, None),
        ("approved_by", "Approved by", "people", 2, None),
        ("order_date", "Order date", "date", 2, None),
        ("expected_delivery", "Expected delivery", "date", 2, None),
        ("sent_date", "Sent date", "date", 2, None),
        ("po_document", "PO document", "file", 2, None),
        ("subtotal", "Subtotal", "mirror", 5, None),
        ("tax_shipping", "Tax / Shipping", "numbers", 2, USD),
        ("total", "Total", "formula", 5, None),
        ("delivery_state", "Delivery state", "formula", 5, None),
        ("notes_to_supplier", "Notes to supplier", "long_text", 2, None),
    ],
    "PO lines": [
        ("product", "Product", "board_relation", 4, None),
        ("uom", "UoM", "mirror", 5, None),
        ("pack_size", "Pack size", "mirror", 5, None),
        ("supplier_part", "Supplier Part #", "mirror", 5, None),
        ("qty_ordered", "Qty ordered", "numbers", 3, None),
        ("packs", "Packs", "formula", 5, None),
        ("unit_price", "Unit price", "numbers", 3, USD),
        ("line_total", "Line total", "formula", 5, None),
        ("qty_received", "Qty received", "numbers", 3, None),
        ("date0", "Received date", "date", 3, None),
        # Built by Omer in the UI (2026-10-28): two-way -> Units + Projects. Replaces the spec's
        # one-way "Project" (deleted).
        ("board_relation_mm8jy91z", "Project \\ Unit", "board_relation", 4, None),
        (None, "Request line", "reflection", 4, {"from": ("Request lines", "po_line")}),
        ("status", "Line status", "status", 3, status(
            ("Open", "grey"), ("Partially Received", "orange"), ("Received", "green", True),
            ("Cancelled", "dark grey"))),
    ],
    "Stock Movements": [
        ("movement_no", "Movement #", "auto_number", 2, {"scope": "board", "order": "ascending"}),
        ("product", "Product", "board_relation", 4, None),
        ("uom", "UoM", "mirror", 5, None),
        ("movement_type", "Movement type", "status", 2, status(
            ("Opening", "dark green"), ("Receipt", "green"), ("Issue to project", "blue"),
            ("Manual in", "light green"), ("Manual out", "orange"), ("Stock count", "purple"))),
        ("qty", "Qty", "numbers", 2, None),
        ("counted_qty", "Counted qty", "numbers", 2, None),
        ("reason", "Reason", "dropdown", 2, dropdown(["Return", "Found", "Damage/Scrap", "Sample", "Other"], single=True)),
        ("note", "Note", "long_text", 2, None),
        ("status", "Status", "status", 2, status(("Pending", "grey"), ("Applied", "green"), ("Rejected", "red"))),
        ("rejection_reason", "Rejection reason", "text", 2, None),
        ("qty_before", "Qty before", "numbers", 2, None),
        ("qty_after", "Qty after", "numbers", 2, None),
        ("applied_at", "Applied at", "date", 2, {"show_time_by_default": True}),
        ("applied_in", "⚙️ Applied in → Product", "board_relation", 4, None),
        ("applied_out", "⚙️ Applied out → Product", "board_relation", 4, None),
        ("unit_project", "Unit / Project", "board_relation", 4, None),
        ("request_line", "Request line", "board_relation", 4, None),
        ("po_line", "PO line", "board_relation", 4, None),
        ("created_by", "Created by", "creation_log", 2, None),
    ],
}

# Default subitem columns repurposed (CLAUDE.md §6): Request lines status -> Decision;
# PO lines status -> Line status, date0 -> Received date. Others renamed zz-unused.
UNUSED_DEFAULTS = {"Request lines": {"person": "Owner", "date0": "Date"}, "PO lines": {}}  # PO lines Owner deleted by Omer

# Subitem boards hang off these parents.
SUBITEM_BOARDS = {"Request lines": "Material Requests", "PO lines": "Purchase Orders"}
