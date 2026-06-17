import frappe

import erpnext.accounts.doctype.account.account as _erpnext_account


def _noop():
    return


def _call_without_idle_check(func, *args, **kwargs):
    original = _erpnext_account._ensure_idle_system
    _erpnext_account._ensure_idle_system = _noop
    try:
        return func(*args, **kwargs)
    finally:
        _erpnext_account._ensure_idle_system = original


@frappe.whitelist()
def update_account_number(name, account_name, account_number=None, from_descendant=False):
    return _call_without_idle_check(
        _erpnext_account.update_account_number,
        name,
        account_name,
        account_number=account_number,
        from_descendant=from_descendant,
    )


@frappe.whitelist()
def merge_account(old, new):
    return _call_without_idle_check(_erpnext_account.merge_account, old, new)
