# Copyright (c) 2024, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.integrations.doctype.whatsapp_settings.whatsapp_settings import send_whatsapp
from frappe.model.document import Document


class WhatsappMessageLog(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		message: DF.Text | None
		recipient: DF.Data | None
		send_now: DF.Check
		status: DF.Literal["Queued", "Sent"]
	# end: auto-generated types
	pass

	@staticmethod
	def clear_old_logs(days=30):
		from frappe.query_builder import Interval
		from frappe.query_builder.functions import Now

		table = frappe.qb.DocType("Whatsapp Message Log")
		frappe.db.delete(
			table, filters=(table.modified < (Now() - Interval(days=days)), table.status == "Sent")
		)


def send_batch():
	settings = frappe.get_single("WhatsApp Settings")
	# triggered every 3 hours (see hooks.py)
	# so we try to use that timespan as much as possible
	# given the sprint, pause and wait config
	sprint = settings.work_sprint or 1080
	pause = settings.pause or 480
	wait = settings.message_cadence or 5

	n = sprint / (wait + 1)  # assuming sending takes 1 s
	s = (60 * 60 * 3) / (sprint + pause)
	d = 0.9

	estimated_capacity = int(n * s * d)

	wmls = frappe.get_list(
		"Whatsapp Message Log",
		filters={"status": "Queued", "send_now": False},
		fields=["name", "message", "recipient"],
		order_by="creation asc",  # Oldest first
		limit=estimated_capacity,
	)
	send_whatsapp(map(lambda r: (r["name"], r["recipient"], r["message"]), wmls))


def send_missing_send_now():
	wmls = frappe.get_list(
		"Whatsapp Message Log",
		filters={"status": "Queued", "send_now": True},
		fields=["name", "message", "recipient"],
		order_by="creation asc",  # Oldest first
	)
	if not wmls:
		return
	send_whatsapp(map(lambda r: (r["name"], r["recipient"], r["message"]), wmls))
