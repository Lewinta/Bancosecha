"""
Create dummy Safe Entry documents (workflow_state="Rejected", no Journal Entry)
to bring a cost center's denomination totals to a desired target.

Usage:
    bench --site <site> execute \\
        bancosecha.bancosecha.maintenance.safe_adjustment.adjust_to_target \\
        --kwargs "{'targets': {...}, 'cash_account': '1210 - CF Bank Bancosecha LLC - B', 'dry_run': True}"

`targets` is a dict mapping cost center to a dict of denomination field -> qty.
Any denomination field omitted is treated as 0 (target = 0).
"""

import frappe
from frappe.utils import today


DENOMINATION_FIELDS = (
    "_10000", "_5000", "_2000", "_1000", "_500",
    "_100", "_050", "_025", "_010", "_005", "_001",
)

DENOMINATION_VALUE = {
    "_10000": 100.00,
    "_5000": 50.00,
    "_2000": 20.00,
    "_1000": 10.00,
    "_500": 5.00,
    "_100": 1.00,
    "_050": 0.50,
    "_025": 0.25,
    "_010": 0.10,
    "_005": 0.05,
    "_001": 0.01,
}


def adjust_to_target(targets, cash_account, dry_run=True, remarks="Denomination adjustment"):
    dry_run = _to_bool(dry_run)
    created = []

    for cost_center, target in targets.items():
        full_target = {f: int(target.get(f) or 0) for f in DENOMINATION_FIELDS}
        current = _current_totals(cost_center)
        deltas = {f: full_target[f] - current[f] for f in DENOMINATION_FIELDS}

        deposit = {f: d for f, d in deltas.items() if d > 0}
        withdraw = {f: -d for f, d in deltas.items() if d < 0}

        print(f"\n=== {cost_center} ===")
        _print_row("Current", current)
        _print_row("Target ", full_target)
        _print_row("Delta  ", deltas)

        safe_account = frappe.db.get_value("Cost Center", cost_center, "custom_safe_account")
        if not safe_account:
            frappe.throw(f"Cost Center {cost_center} has no custom_safe_account configured.")

        company = frappe.db.get_value("Cost Center", cost_center, "company")

        if not deposit and not withdraw:
            print("  No adjustment needed.")
            continue

        for entry_type, denoms in (("Deposit", deposit), ("Withdrawal", withdraw)):
            if not denoms:
                continue
            total = sum(qty * DENOMINATION_VALUE[f] for f, qty in denoms.items())
            print(f"  Will create {entry_type}: total ${total:,.2f}  denoms={denoms}")

            if dry_run:
                continue

            name = _create_adjustment_safe_entry(
                company=company,
                cost_center=cost_center,
                safe_account=safe_account,
                cash_account=cash_account,
                entry_type=entry_type,
                denoms=denoms,
                remarks=remarks,
            )
            created.append((cost_center, entry_type, name))
            print(f"  Created {entry_type} entry: {name}")

    if dry_run:
        print("\nDRY RUN — no entries created. Re-run with dry_run=False to apply.")
    else:
        print(f"\nCreated {len(created)} Safe Entry document(s):")
        for cc, t, n in created:
            print(f"  - {n}  ({cc}, {t})")

    return created


def _current_totals(cost_center):
    sums = ", ".join(
        f"COALESCE(SUM(CASE WHEN type='Deposit' THEN {f} ELSE -{f} END), 0) AS {f}"
        for f in DENOMINATION_FIELDS
    )
    row = frappe.db.sql(
        f"""
        SELECT {sums}
        FROM `tabSafe Entry`
        WHERE docstatus = 1
          AND workflow_state = 'Approved'
          AND cost_center = %(cc)s
        """,
        {"cc": cost_center},
        as_dict=True,
    )[0]
    return {f: int(row.get(f) or 0) for f in DENOMINATION_FIELDS}


def _create_adjustment_safe_entry(company, cost_center, safe_account, cash_account,
                                  entry_type, denoms, remarks):
    doc = frappe.new_doc("Safe Entry")
    doc.update({
        "company": company,
        "cost_center": cost_center,
        "type": entry_type,
        "safe_account": safe_account,
        "cash_account": cash_account,
        "posting_date": today(),
        "is_adjustment": 1,
        "workflow_state": "Requested",
    })
    for f, qty in denoms.items():
        doc.set(f, qty)
    doc.total_amount = sum(qty * DENOMINATION_VALUE[f] for f, qty in denoms.items())
    doc.insert(ignore_permissions=True)

    doc.workflow_state = "Approved"
    doc.flags.ignore_workflow = True
    doc.submit()
    return doc.name


def _print_row(label, values):
    parts = "  ".join(f"{f}={values[f]:>6}" for f in DENOMINATION_FIELDS)
    print(f"  {label}: {parts}")


def cancel_entries(names, dry_run=True):
    """Cancel a list of Safe Entry adjustments. Sets docstatus=2 and
    workflow_state='Cancelled' directly to bypass workflow transitions."""
    dry_run = _to_bool(dry_run)
    if isinstance(names, str):
        names = [n.strip() for n in names.split(",") if n.strip()]

    for name in names:
        info = frappe.db.get_value(
            "Safe Entry", name,
            ["docstatus", "workflow_state", "is_adjustment", "cost_center", "type", "total_amount"],
            as_dict=True,
        )
        if not info:
            print(f"  {name}: not found")
            continue
        if not info.is_adjustment:
            print(f"  {name}: not an adjustment entry — skipping")
            continue
        if info.docstatus != 1:
            print(f"  {name}: docstatus={info.docstatus} — already cancelled or draft, skipping")
            continue
        print(f"  {name}: {info.cost_center} {info.type} ${info.total_amount:,.2f} → cancel")
        if not dry_run:
            frappe.db.set_value(
                "Safe Entry", name,
                {"docstatus": 2, "workflow_state": "Cancelled"},
                update_modified=False,
            )

    if not dry_run:
        frappe.db.commit()


def _to_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "y", "t")
    return bool(value)
