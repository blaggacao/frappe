# Copyright (c) 2024, Frappe Technologies and contributors
# For license information, please see license.txt

import base64
import time
import urllib.parse
from collections.abc import Iterable
from contextlib import closing
from io import BytesIO
from random import randint
from typing import Union, overload

import qrcode
import requests
import requests_unixsocket
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.colormasks import (
	HorizontalGradiantColorMask,
	ImageColorMask,
	RadialGradiantColorMask,
	SquareGradiantColorMask,
	VerticalGradiantColorMask,
)
from qrcode.image.styles.moduledrawers import (
	CircleModuleDrawer,
	GappedSquareModuleDrawer,
	HorizontalBarsDrawer,
	RoundedModuleDrawer,
	SquareModuleDrawer,
	VerticalBarsDrawer,
)

import frappe
from frappe import _
from frappe.model.document import Document


class WhatsAppSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		cadence_jitter: DF.Int
		jid: DF.Data | None
		message_cadence: DF.Int
		pause: DF.Int
		pause_jitter: DF.Int
		server: DF.Data
		work_sprint: DF.Int
		work_sprint_jitter: DF.Int
	# end: auto-generated types

	def _post(self, cmd) -> str | None:
		if not self.get("_session"):
			if self.server.startswith("/"):
				self._server = "http+unix://" + urllib.parse.quote_plus(self.server)
				self._session = requests_unixsocket.Session()
			else:
				self._server = self.server
				self._session = requests.Session()
			self._server += "/command"
		try:
			res = self._session.post(self._server, json=cmd, timeout=5)
			res.raise_for_status()
		# This will raise an exception if the status code is not in the 200-299 range
		except requests.exceptions.HTTPError as e:
			self.log_error("Sending Failed", e)
			return
		except Exception as e:
			frappe.throw(_("Connectivity issue with whatsmeow server: {}").format(e))
		else:
			return res.text

	@property
	def jid(self):
		try:
			return self.whoami()
		except Exception:
			return

	@frappe.whitelist()
	def logout(self):
		if not self.server:
			return
		self._post({"cmd": "logout"})

	@frappe.whitelist()
	def whoami(self):
		if not self.server:
			return
		return self._post({"cmd": "whoami"})

	@frappe.whitelist()
	def pair(self):
		# qr codes are dispached upon login
		res = self._post({"cmd": "reconnect"})

		qr = qrcode.QRCode(version=7, box_size=6, border=3)
		qr.add_data(res)
		qr.make(fit=True)
		img = qr.make_image(
			image_factory=StyledPilImage,
			color_mask=RadialGradiantColorMask(
				back_color=(255, 255, 255), center_color=(70, 130, 180), edge_color=(0, 0, 0)
			),
			module_drawer=GappedSquareModuleDrawer(),
			eye_drawer=SquareModuleDrawer(),
		)
		temp = BytesIO()
		img.save(temp, "PNG")
		temp.seek(0)
		b64 = base64.b64encode(temp.read())
		return "data:image/png;base64,{}".format(b64.decode("utf-8"))


def enqueue_whatsapp(messages: Iterable[tuple[str, str]], try_send_now=False) -> None:
	if try_send_now:
		send_now = []
		for message, recipient in messages:
			wml = frappe.new_doc("Whatsapp Message Log")
			wml.update(
				{
					"message": message,
					"recipient": recipient,
					"status": "Queued",
				}
			)
			wml.insert(ignore_permissions=True)
			send_now.append((wml.name, recipient, message))

		from frappe.utils.background_jobs import enqueue

		enqueue(
			method=send_whatsapp,
			queue="long",
			messages=send_now,
		)
	else:
		frappe.db.bulk_insert(
			"Whatsapp Message Log",
			["message", "recipient", "status", "name"],
			map(lambda t: (*t, "Queued", hash("".join(t))), messages),
			ignore_duplicates=True,
		)


def send_whatsapp(messages: Iterable[tuple[str, str] | tuple[str, str, str]]) -> None:
	settings = frappe.get_single("WhatsApp Settings")

	if not settings.jid:
		frappe.throw(_("WhatsApp currently not linked: please revise WhatsApp Settings"))

	wait = settings.message_cadence or 5
	jitter = settings.cadence_jitter or 2
	sprint = settings.work_sprint or 1080
	sprint_jitter = settings.work_sprint_jitter or 300
	pause = settings.pause or 480
	pause_jitter = settings.pause_jitter or 180

	start_time = time.time()

	needs_pause = randint(
		sprint - sprint_jitter,
		sprint + sprint_jitter,
	)
	pause = randint(
		pause - pause_jitter,
		pause + pause_jitter,
	)
	for tup in messages:
		if isinstance(tup, tuple) and len(tup) == 2:
			# Handle 2-item tuple
			recp, msg = tup
			wml = None
		elif isinstance(tup, tuple) and len(tup) == 3:
			# Handle 3-item tuple
			wml, recp, msg = tup
			# guard against parallel processing of a queue item
			# by the background and by the immediate send
			status = frappe.db.get_value("Whatsapp Message Log", wml, "status")
			if status == "Sent":
				continue
		success = settings._post({"cmd": "send", "args": [recp, msg]})
		if wml and success is not None:
			frappe.db.set_value("Whatsapp Message Log", wml, "status", "Sent")
			frappe.db.commit()  # ensure status is persistet
		time.sleep(randint(wait - jitter, wait + jitter))
		if time.time() - start_time > needs_pause:
			time.sleep(pause)
			start_time = time.time()
			needs_pause = randint(
				sprint - sprint_jitter,
				sprint + sprint_jitter,
			)
			pause = randint(
				pause - pause_jitter,
				pause + pause_jitter,
			)
