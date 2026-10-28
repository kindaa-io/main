"""Phase 9.1–9.2: one-page mock PDF for PO-0003, watermarked. Local only; upload is phase9_upload."""
import datetime
import json
import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "PO-0003-mock.pdf")
T = datetime.date(2026, 10, 28)
D = json.load(open(os.path.join(ROOT, "data", "sample-data.json")))


def d(off):
    return (T + datetime.timedelta(days=off)).strftime("%b %d, %Y")


def money(x):
    return "${:,.2f}".format(x)


def main():
    po = D["pos"]["PO-0003"]
    sup = D["suppliers"][po[2]]
    lines = [(k, v) for k, v in D["po_lines"].items() if k.startswith("PO-0003/")]
    c = canvas.Canvas(OUT, pagesize=letter)
    w, h = letter
    c.setTitle("PO-0003 — SAMPLE LAYOUT")

    # Watermark first, so the content prints over it
    c.saveState()
    c.setFillColor(colors.Color(0.85, 0.1, 0.1, alpha=0.18))
    c.setFont("Helvetica-Bold", 28)
    c.translate(w / 2, h / 2)
    c.rotate(45)
    c.drawCentredString(0, 0, "SAMPLE LAYOUT – PENDING RICCO TEMPLATE")
    c.restoreState()

    x0, y = 0.8 * inch, h - 0.9 * inch
    c.setFont("Helvetica-Bold", 18)
    c.drawString(x0, y, "Ricco Cabinetry — Purchase Order")
    c.setFont("Helvetica-Bold", 13)
    c.drawRightString(w - x0, y, "PO-0003")
    y -= 0.35 * inch
    c.setFont("Helvetica", 10)
    c.drawString(x0, y, "Order date: %s" % d(po[4]))
    c.drawRightString(w - x0, y, "Expected delivery: %s" % d(po[5]))

    y -= 0.5 * inch
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x0, y, "Supplier")
    c.setFont("Helvetica", 10)
    phone = sup[3]
    phone = "(%s) %s-%s" % (phone[2:5], phone[5:8], phone[8:])
    for i, line in enumerate([sup[0], "Attn: " + sup[1], sup[2], phone, "Payment terms: " + sup[4]]):
        c.drawString(x0, y - 14 * (i + 1), line)

    y -= 1.35 * inch
    cols = [("Product", x0), ("Part #", x0 + 2.6 * inch), ("Packs", x0 + 4.05 * inch),
            ("Qty", x0 + 4.75 * inch), ("Unit price", x0 + 5.45 * inch), ("Line total", w - x0)]
    c.setFillColor(colors.Color(0.93, 0.93, 0.93))
    c.rect(x0 - 4, y - 5, w - 2 * x0 + 8, 18, stroke=0, fill=1)
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 9.5)
    for i, (label, x) in enumerate(cols):
        (c.drawString if i < 2 else c.drawRightString)(x if i < 2 else (x + 0.45 * inch if i < 5 else x), y, label)
    c.setFont("Helvetica", 9.5)
    subtotal = 0
    for _ref, (p, qty, price, *_r) in lines:
        prod = D["products"][p]
        packs = qty / prod[4] if prod[4] else ""
        total = qty * price
        subtotal += total
        y -= 18
        vals = [prod[0], prod[6], "%g" % packs, "%g" % qty, money(price), money(total)]
        for i, (v, (_l, x)) in enumerate(zip(vals, cols)):
            (c.drawString if i < 2 else c.drawRightString)(x if i < 2 else (x + 0.45 * inch if i < 5 else x), y, v)
    y -= 10
    c.line(x0 - 4, y, w - x0 + 4, y)
    tax = po[7]
    for label, val, bold in (("Subtotal", subtotal, False), ("Tax / Shipping", tax, False), ("Total", subtotal + tax, True)):
        y -= 16
        c.setFont("Helvetica-Bold" if bold else "Helvetica", 10)
        c.drawRightString(w - x0 - 1.3 * inch, y, label)
        c.drawRightString(w - x0, y, money(val))

    c.setFont("Helvetica-Oblique", 8)
    c.setFillColor(colors.grey)
    c.drawString(x0, 0.6 * inch, "Demo document generated from sample data. Not a real purchase order.")
    c.showPage()
    c.save()
    print("written", OUT, "subtotal", subtotal, "total", subtotal + tax)


if __name__ == "__main__":
    main()
