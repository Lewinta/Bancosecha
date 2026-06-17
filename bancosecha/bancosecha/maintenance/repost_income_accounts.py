"""
Realign Sales Invoice item income accounts with the current Item Default and
repost their GL Entries.

Usage:
    bench --site <site> execute \\
        bancosecha.bancosecha.maintenance.repost_income_accounts.run \\
        --kwargs "{'from_date': '2026-03-15', 'dry_run': True}"

When dry_run is False the script:
  1. UPDATEs `tabSales Invoice Item.income_account` for every line whose item
     has a different `income_account` set in `tabItem Default` for the
     invoice's company.
  2. Creates "Repost Accounting Ledger" documents in chunks and submits them.
     Submissions with more than 5 vouchers are processed asynchronously by
     ERPNext, so the actual repost work happens in the background queue.
"""

from collections import Counter

import frappe


AFFECTED_LINES_SQL = """
    SELECT
        si.name        AS invoice,
        si.posting_date AS posting_date,
        si.company     AS company,
        sii.name       AS line,
        sii.item_code  AS item_code,
        sii.income_account AS old_account,
        id.income_account  AS new_account
    FROM `tabSales Invoice` si
    JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
    JOIN `tabItem Default` id
        ON id.parent = sii.item_code
       AND id.company = si.company
    WHERE si.docstatus = 1
      AND si.posting_date >= %(from_date)s
      AND id.income_account IS NOT NULL
      AND id.income_account != ''
      AND id.income_account != sii.income_account
    ORDER BY si.posting_date, si.name, sii.idx
"""


def run(from_date="2026-03-15", dry_run=True, batch_size=30, limit=None):
    """Entry point. See module docstring."""
    dry_run = _to_bool(dry_run)
    batch_size = int(batch_size)
    if limit is not None:
        limit = int(limit)

    rows = frappe.db.sql(AFFECTED_LINES_SQL, {"from_date": from_date}, as_dict=True)
    if not rows:
        print("Nothing to do — no Sales Invoice lines differ from current Item Default.")
        return

    invoices = []
    seen = set()
    for r in rows:
        if r.invoice not in seen:
            seen.add(r.invoice)
            invoices.append(r.invoice)

    if limit:
        invoices = invoices[:limit]
        keep = set(invoices)
        rows = [r for r in rows if r.invoice in keep]

    _print_summary(rows, invoices, from_date)

    if dry_run:
        print("\nDRY RUN — no changes applied. Re-run with dry_run=False to apply.")
        return

    print(f"\nUpdating income_account on {len(rows)} invoice lines...")
    _update_invoice_lines(rows)
    frappe.db.commit()
    print("Income accounts updated.")

    print(f"\nQueueing repost in batches of {batch_size}...")
    repost_docs = _queue_reposts(invoices, batch_size)
    frappe.db.commit()
    print(f"Submitted {len(repost_docs)} Repost Accounting Ledger documents.")
    for name, count in repost_docs:
        print(f"  - {name}: {count} invoices")
    print("\nReposts >5 vouchers run in the background queue. Monitor with:")
    print("  bench --site <site> show-pending-tasks")
    print("Or check 'Repost Accounting Ledger' list in Desk.")


def _print_summary(rows, invoices, from_date):
    print(f"From date: {from_date}")
    print(f"Affected invoice lines: {len(rows)}")
    print(f"Affected invoices: {len(invoices)}")

    print("\nBreakdown by item / account move:")
    grouped = Counter(
        (r.item_code, r.old_account, r.new_account, r.company) for r in rows
    )
    width = max(len(k[0]) for k in grouped.keys())
    for (item, old, new, company), count in grouped.most_common():
        print(f"  {item.ljust(width)}  {old} → {new}  ({company})  [{count} lines]")


def _update_invoice_lines(rows):
    for r in rows:
        frappe.db.set_value(
            "Sales Invoice Item",
            r.line,
            "income_account",
            r.new_account,
            update_modified=False,
        )


def _queue_reposts(invoices, batch_size):
    submitted = []
    for start in range(0, len(invoices), batch_size):
        chunk = invoices[start:start + batch_size]
        company = frappe.db.get_value("Sales Invoice", chunk[0], "company")
        rdoc = frappe.new_doc("Repost Accounting Ledger")
        rdoc.company = company
        for inv in chunk:
            rdoc.append("vouchers", {
                "voucher_type": "Sales Invoice",
                "voucher_no": inv,
            })
        rdoc.insert(ignore_permissions=True)
        rdoc.submit()
        submitted.append((rdoc.name, len(chunk)))
        frappe.db.commit()
    return submitted


def _to_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "y", "t")
    return bool(value)
