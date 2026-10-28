"""demo-spec.md §9.2–9.6 as data (MR-6 excluded per Omer, D-08). Writes data/sample-data.json.
Dates are offsets from T (build day). Real items are placeholders resolved from id-map.json."""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SUPPLIERS = {
    "S1": ("Pacific Panel Supply", "Dana Whitfield", "orders@pacificpanel.example", "+15550102101", "Net 30", ["Sheet Goods"]),
    "S2": ("Edge & Trim Distributors", "Luis Romero", "sales@edgetrim.example", "+15550102202", "Net 30", ["Edgeband"]),
    "S3": ("Hardware Source Co.", "Priya Nair", "orders@hardwaresource.example", "+15550102303", "Net 15",
           ["Hinges", "Slides & Hardware", "Accessories"]),
    "S4": ("Coastline Coatings", "Mark Ellison", "orders@coastlinecoatings.example", "+15550102404", "COD", ["Finish / Paint"]),
}

# ref: name, group/category, uom, stock type, pack, supplier, part, min, last price
PRODUCTS = {
    "P01": ('MDF 3/4" 4x8 White Melamine', "Sheet Goods", "sheet", "Stocked", 1, "S1", "PPS-MDF34-WM", 100, 68.00),
    "P02": ('MDF 3/4" 4x8 Raw (Paint Grade)', "Sheet Goods", "sheet", "Stocked", 1, "S1", "PPS-MDF34-RAW", 25, 52.00),
    "P03": ('Plywood 3/4" 4x8 Maple Pre-finished', "Sheet Goods", "sheet", "Stocked", 1, "S1", "PPS-PLY34-MPF", 15, 95.00),
    "P04": ('Plywood 1/4" 4x8 Maple Pre-finished', "Sheet Goods", "sheet", "Stocked", 1, "S1", "PPS-PLY14-MPF", 10, 38.00),
    "P05": ("Edgeband White PVC 22mm", "Edgeband", "ft", "Stocked", 300, "S2", "ET-PVC22-WH", 600, 0.12),
    "P06": ("Edgeband Maple Wood 22mm", "Edgeband", "ft", "Order-to-project", 300, "S2", "ET-WD22-MP", 0, 0.35),
    "P07": ("Hinge 110° Soft-close Full Overlay", "Hinges", "each", "Stocked", 50, "S3", "HS-H110-FO", 200, 3.10),
    "P08": ("Hinge Mounting Plate 0mm", "Hinges", "each", "Stocked", 50, "S3", "HS-MP0", 200, 0.90),
    "P09": ('Drawer Slide 21" Undermount Soft-close', "Slides & Hardware", "pair", "Stocked", 10, "S3", "HS-UM21-SC", 40, 24.50),
    "P10": ('Drawer Slide 18" Undermount Soft-close', "Slides & Hardware", "pair", "Order-to-project", 10, "S3", "HS-UM18-SC", 0, 22.00),
    "P11": ("Pull Handle 128mm Matte Black", "Accessories", "each", "Order-to-project", 25, "S3", "HS-PH128-MB", 0, 4.20),
    "P12": ("Shelf Pin 5mm Nickel", "Accessories", "each", "Stocked", 1000, "S3", "HS-SP5-NI", 500, 0.04),
    "P13": ("Primer White 1 gal", "Finish / Paint", "gallon", "Stocked", 1, "S4", "CC-PRM-WH-1G", 10, 32.00),
    "P14": ("Pre-cat Lacquer Satin 1 gal", "Finish / Paint", "gallon", "Stocked", 1, "S4", "CC-PCL-SAT-1G", 5, 48.00),
    "P15": ('Toe Kick 4" Black Melamine 8ft', None, None, "Order-to-project", None, None, None, None, None),
}

# MR: (link placeholder, status, group, submitted, needed by, POs, note, lines)
# line: (product, qty req, decision, reserved, to order, issued, PO line ref)
REQUESTS = {
    "MR-1": ("PRJ_A", "Closed", "Closed & cancelled", -28, -20, [], "L5: 10 pairs used, 2 released back to stock.", [
        ("P01", 30, "Issued", 0, 0, 30, None), ("P05", 400, "Issued", 0, 0, 400, None),
        ("P07", 60, "Issued", 0, 0, 60, None), ("P08", 60, "Issued", 0, 0, 60, None),
        ("P09", 12, "Issued", 0, 0, 10, None)]),
    "MR-2": ("PRJ_B_UNIT_1", "Ready for Production", "Active requests", -14, 3, ["PO-0001", "PO-0002"], None, [
        ("P03", 20, "From Stock", 20, 0, None, None), ("P04", 8, "From Stock", 8, 0, None, None),
        ("P06", 600, "Received", 600, 600, None, "PO-0001/L1"), ("P07", 40, "From Stock", 40, 0, None, None),
        ("P08", 40, "From Stock", 40, 0, None, None), ("P11", 30, "Received", 30, 30, None, "PO-0002/L1")]),
    "MR-3": ("PRJ_C_UNIT_1", "Waiting for Delivery", "Active requests", -10, 5, ["PO-0003", "PO-0004"], None, [
        ("P02", 50, "From Stock", 50, 0, None, None), ("P13", 20, "Ordered", 16, 4, None, "PO-0003/L1"),
        ("P10", 16, "Ordered", 10, 16, None, "PO-0004/L1"), ("P14", 6, "From Stock", 6, 0, None, None)]),
    "MR-4": ("PRJ_A_UNIT_2", "Issue Materials", "Active requests", -21, -2, [],
             "Trigger for Issue Materials = production complete — TBD with Sam.", [
        ("P01", 24, "From Stock", 24, 0, 24, None), ("P05", 300, "From Stock", 300, 0, 300, None),
        ("P12", 200, "From Stock", 200, 0, 200, None), ("P07", 30, "From Stock", 30, 0, 30, None)]),
    "MR-5": ("PRJ_C", "In Review", "Active requests", -1, 14, [],
             "L2 product is new — purchaser to complete supplier/UoM/price before ordering.", [
        ("P01", 60, "From Stock", 60, 0, None, None), ("P15", 6, "To Order", 0, 6, None, None),
        ("P09", 24, "From Stock", 24, 0, None, None), ("P14", 10, "Partial", 6, 4, None, None)]),
}

# PO: (n, status, group, supplier, project placeholder, order, expected, sent, tax, note, approved)
POS = {
    "PO-0001": ("Received", "Closed & cancelled", "S2", "PRJ_B", -13, -6, -13, 25, None),
    "PO-0002": ("Received", "Closed & cancelled", "S3", "PRJ_B", -13, -5, -13, 15, None),
    "PO-0003": ("Sent", "Open POs", "S4", "PRJ_C", -9, -2, -9, 40, None),
    "PO-0004": ("Partially Received", "Open POs", "S3", "PRJ_C", -9, 4, -9, 30, None),
    "PO-0005": ("Draft", "Open POs", "S1", None, None, None, None, 0, "Replenishment — MDF white below minimum."),
}
# PO line: (product, qty ordered, unit price, qty received, received date, project placeholder, line status, request line)
PO_LINES = {
    "PO-0001/L1": ("P06", 600, 0.35, 600, -6, "PRJ_B", "Received", "MR-2/L3"),
    "PO-0002/L1": ("P11", 50, 4.20, 50, -5, "PRJ_B", "Received", "MR-2/L6"),
    "PO-0003/L1": ("P13", 4, 32.00, 0, None, "PRJ_C", "Open", "MR-3/L2"),
    "PO-0003/L2": ("P13", 12, 32.00, 0, None, None, "Open", None),
    "PO-0004/L1": ("P10", 20, 22.00, 10, -3, "PRJ_C", "Partially Received", "MR-3/L3"),
    "PO-0004/L2": ("P09", 20, 24.50, 0, None, None, "Open", None),
    "PO-0005/L1": ("P01", 100, 68.00, 0, None, None, "Open", None),
}

# SM: (type, product, qty, counted, reason, before, after, link, unit/project, request line, PO line, date, status, note, rejection)
M = []
for i, (p, q) in enumerate([("P01", 150), ("P02", 80), ("P03", 40), ("P04", 25), ("P05", 1500), ("P07", 400),
                            ("P08", 400), ("P09", 60), ("P12", 2000), ("P13", 14), ("P14", 12)], start=1):
    M.append(("SM-%02d" % i, "Opening", p, q, None, None, 0, q, "in", None, None, None, -45, "Applied", None, None))
for i, (p, q, b, a, ln) in enumerate([("P01", 30, 150, 120, "MR-1/L1"), ("P05", 400, 1500, 1100, "MR-1/L2"),
                                      ("P07", 60, 400, 340, "MR-1/L3"), ("P08", 60, 400, 340, "MR-1/L4"),
                                      ("P09", 10, 60, 50, "MR-1/L5")], start=12):
    M.append(("SM-%02d" % i, "Issue to project", p, q, None, None, b, a, "out", "PRJ_A", ln, None, -20, "Applied", None, None))
M += [
    ("SM-17", "Manual in", "P13", 2, None, "Return", 14, 16, "in", None, None, None, -18, "Applied", None, None),
    ("SM-18", "Manual out", "P03", 2, None, "Damage/Scrap", 40, 38, "out", None, None, None, -16, "Applied", "Water damage, 2 sheets.", None),
    ("SM-19", "Stock count", "P12", 150, 1850, None, 2000, 1850, "out", None, None, None, -15, "Applied", "Quarterly count.", None),
    ("SM-20", "Receipt", "P06", 600, None, None, 0, 600, "in", "PRJ_B_UNIT_1", "MR-2/L3", "PO-0001/L1", -6, "Applied", None, None),
    ("SM-21", "Receipt", "P11", 50, None, None, 0, 50, "in", "PRJ_B_UNIT_1", "MR-2/L6", "PO-0002/L1", -5, "Applied", None, None),
    ("SM-22", "Receipt", "P10", 10, None, None, 0, 10, "in", "PRJ_C_UNIT_1", "MR-3/L3", "PO-0004/L1", -3, "Applied", None, None),
    ("SM-23", "Manual out", "P01", 50, None, "Damage/Scrap", None, None, None, None, None, None, -1, "Rejected", None,
     "Exceeds Available (36). Reserved stock can't be taken manually."),
]

# §9.7 with MR-6 removed (D-08): P04 reserved 10→8, P07 74→70.
EXPECTED = {
    "catalogue": {"P01": (120, 84, 36, "Low"), "P02": (80, 50, 30, "In"), "P03": (38, 20, 18, "In"),
                  "P04": (25, 8, 17, "In"), "P05": (1100, 300, 800, "In"), "P06": (600, 600, 0, "—"),
                  "P07": (340, 70, 270, "In"), "P08": (340, 40, 300, "In"), "P09": (50, 24, 26, "Low"),
                  "P10": (10, 10, 0, "—"), "P11": (50, 30, 20, "—"), "P12": (1850, 200, 1650, "In"),
                  "P13": (16, 16, 0, "Out"), "P14": (12, 12, 0, "Out"), "P15": (0, 0, 0, "—")},
    "material_cost": {"MR-1": 2573.00, "MR-2": 2700.00, "MR-3": 3880.00, "MR-4": 1769.00, "MR-5": 5148.00},
    "po": {"PO-0001": (210, 235, ""), "PO-0002": (210, 225, ""), "PO-0003": (512, 552, "Overdue"),
           "PO-0004": (930, 960, ""), "PO-0005": (6800, 6800, "")},
    "supplier_total": {"S1": 6800, "S2": 235, "S3": 1185, "S4": 552},
    "projects": {"PRJ_A": {"material_cost": 2573.00, "units_cost_includes": 1769.00},
                 "PRJ_B": {"units_cost_includes": 2700.00},
                 "PRJ_C": {"material_cost": 5148.00, "units_cost_includes": 3880.00}},
}

if __name__ == "__main__":
    out = {"suppliers": SUPPLIERS, "products": PRODUCTS, "requests": REQUESTS, "pos": POS, "po_lines": PO_LINES,
           "movements": M, "expected": EXPECTED}
    with open(os.path.join(ROOT, "data", "sample-data.json"), "w") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    print("written", {k: len(v) for k, v in out.items()})
