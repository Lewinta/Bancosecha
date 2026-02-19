# -*- coding: utf-8 -*-
# Copyright (c) 2020, Youssef Restom and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe import qb
from frappe.utils import cint
from frappe.model.document import Document
from bancosecha.bancosecha.api.status_updater import StatusUpdater


class POSOpeningShift(StatusUpdater):
	def validate(self):
		self.validate_pos_profile_and_cashier()
		self.set_status()
		self.validate_duplicate()

	def validate_pos_profile_and_cashier(self):
		if self.company != frappe.db.get_value("POS Profile", self.pos_profile, "company"):
			frappe.throw(_("POS Profile {} does not belongs to company {}".format(self.pos_profile, self.company)))

		if not cint(frappe.db.get_value("User", self.user, "enabled")):
			frappe.throw(_("User {} has been disabled. Please select valid user/cashier".format(self.user)))

	def on_submit(self):
		self.set_status(update=True)
	
	def validate_duplicate(self):
		# Check for existing open shift for the same POS Profile and User
		OS = qb.DocType("POS Opening Shift")
		existing_shift = qb.from_(OS).select(
			OS.name
		).where(
			(OS.pos_profile == self.pos_profile) &
			(OS.user == self.user) &
			(OS.posting_date == self.posting_date) &
			(OS.status == "Open") &
			(OS.name != self.name)
		).limit(1).run(as_dict=True)

		if existing_shift:
			frappe.throw(_("An open POS Opening Shift <b>{}</b> already exists for POS Profile <b>{}</b> on date <b>{}</b>.".format(
				existing_shift[0].name, self.pos_profile, frappe.format_value(self.posting_date, {"fieldtype": "Date"})
			)))
	@frappe.whitelist()
	def set_default_pos_profile(self):
		# POS Profile User
		PU = qb.DocType("POS Profile User")
		PP = qb.DocType("POS Profile")
		PM = qb.DocType("POS Payment Method")
		MP = qb.DocType("Mode of Payment")

		default_pos_profile = qb.from_(PU).join(PP).on(
			(PU.parent == PP.name)&
			(PU.default == 1)&
			(PU.user == frappe.session.user)
		).join(PM).on(
			(PM.parent == PP.name)
		).join(MP).on(
			(PM.mode_of_payment == MP.name)
		).select(
			PP.name,
			MP.name.as_("mode_of_payment"),
			MP.type
		).where(
			(PM.default == 1)&
			(MP.enabled == 1)&
			(PP.disabled == 0)
		).limit(1).run(as_dict=True)

		if default_pos_profile:
			self.pos_profile = default_pos_profile[0].name
			self.set("balance_details", [])
			self.append("balance_details", {
				"mode_of_payment": default_pos_profile[0].mode_of_payment,
				"type": default_pos_profile[0].type,
				"opening_balance": 0.0
			})
