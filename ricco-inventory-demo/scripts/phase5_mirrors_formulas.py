"""Phase 5.3: mirrors and formulas on the demo boards, in dependency order. Idempotent."""
import json
import mlib
import columns

PHASE = "5"


def cmap():
    return mlib.load_json(mlib.COLUMN_MAP, {})["boards"]


def col_id(board, title):
    return cmap()[board]["columns"][title]["id"]


def bid(board):
    return columns.board_id(board)


def mirror(board, cid, rel_title, src_board, src_col_title, kind):
    """kind: 'sum' (numbers), 'status' (all statuses) or None (text/email/dropdown/connect)."""
    d = {"relation_column": {col_id(board, rel_title): True},
         "displayed_linked_columns": [{"board_id": str(bid(src_board)), "column_ids": [col_id(src_board, src_col_title)]}]}
    if kind == "sum":
        d["function"] = "sum"
    elif kind == "status":
        d["sumType"] = "allStatuses"
    columns.ensure(board, cid, PHASE, defaults=d,
                   note="%s: mirror %s via %s -> %s.%s %s" % (board, cid, rel_title, src_board, src_col_title, kind or ""))


def formula(board, cid, expr):
    columns.ensure(board, cid, PHASE, defaults={"formula": expr}, note="%s: formula %s = %s" % (board, cid, expr))


def refresh(board):
    columns.record_column_map(board, columns.read_columns(bid(board)))


SUBITEMS = "Subitems"  # title of the subtasks column on Material Requests / Purchase Orders

if __name__ == "__main__":
    mlib.check_identity()
    # Catalogue
    B = "Materials Catalogue"
    mirror(B, "supplier_email", "Default supplier", "Suppliers", "Email", None)
    mirror(B, "in_total", "⚙️ Applied in", "Stock Movements", "Qty", "sum")
    mirror(B, "out_total", "⚙️ Applied out", "Stock Movements", "Qty", "sum")
    formula(B, "on_hand", "{in_total} - {out_total}")
    mirror(B, "reserved", "⚙️ Request lines", "Request lines", "Qty reserved", "sum")
    formula(B, "available", "{on_hand} - {reserved}")
    formula(B, "stock_state", 'IF({stock_type}="Order-to-project","—",IF({available}<=0,"Out",'
                              'IF({available}<{minimum_level},"Low","In")))')
    formula(B, "stock_value", "{on_hand} * {last_price}")
    refresh(B)
    # Request lines
    L = "Request lines"
    mirror(L, "uom", "Product", B, "UoM", None)
    mirror(L, "on_hand", "Product", B, "On hand", None)
    mirror(L, "available", "Product", B, "Available", None)
    mirror(L, "supplier", "Product", B, "Default supplier", None)
    formula(L, "qty_outstanding", 'IF(OR({status}="Issued",{status}="Cancelled"),0,'
                                  'MAX(0,{qty_requested}-{qty_reserved}))')
    mirror(L, "qty_ordered", "PO line", "PO lines", "Qty ordered", "sum")
    mirror(L, "qty_received", "PO line", "PO lines", "Qty received", "sum")
    mirror(L, "po_unit_price", "PO line", "PO lines", "Unit price", "sum")
    mirror(L, "est_unit_price", "Product", B, "Last purchase price", "sum")
    formula(L, "line_cost", "IF({qty_issued}>0,{qty_issued},{qty_requested}) * "
                            "IF({po_unit_price}>0,{po_unit_price},{est_unit_price})")
    refresh(L)
    # Requests
    R = "Material Requests"
    mirror(R, "po_status", "Purchase Orders", "Purchase Orders", "Status", "status")
    mirror(R, "material_cost", SUBITEMS, L, "Line cost", "sum")
    refresh(R)
    # PO lines
    PL = "PO lines"
    mirror(PL, "uom", "Product", B, "UoM", None)
    mirror(PL, "pack_size", "Product", B, "Pack size", "sum")
    mirror(PL, "supplier_part", "Product", B, "Supplier Part #", None)
    formula(PL, "packs", 'IF({pack_size}>0,ROUND({qty_ordered}/{pack_size},2),"")')
    formula(PL, "line_total", "{qty_ordered} * {unit_price}")
    refresh(PL)
    # POs
    PO = "Purchase Orders"
    mirror(PO, "supplier_email", "Supplier", "Suppliers", "Email", None)
    mirror(PO, "contact", "Supplier", "Suppliers", "Contact person", None)
    mirror(PO, "subtotal", SUBITEMS, PL, "Line total", "sum")
    formula(PO, "total", "{subtotal} + {tax_shipping}")
    formula(PO, "delivery_state", 'IF(AND({status}<>"Draft",{status}<>"Received",{status}<>"Closed",'
                                  '{status}<>"Cancelled",NOT(ISBLANK({expected_delivery})),'
                                  'DAYS({expected_delivery},TODAY())<0),"Overdue","")')
    refresh(PO)
    # Suppliers
    S_ = "Suppliers"
    mirror(S_, "total_ordered", "Purchase Orders", PO, "Total", "sum")
    mirror(S_, "open_pos", "Purchase Orders", PO, "Status", "status")
    refresh(S_)
    # Movements
    mirror("Stock Movements", "uom", "Product", B, "UoM", None)
    refresh("Stock Movements")
    print("done")
