# Copyright (c) 2025, Lewin Villar and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CheckIssuer(Document):
	def validate(self):
		self.full_name = self.full_name.strip().upper()
