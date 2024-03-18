# Copyright (c) 2024, Frappe Technologies and contributors
# For license information, please see license.txt

import base64
import urllib.parse
from contextlib import closing
from io import BytesIO

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

		jid: DF.Data | None
		server: DF.Data
	# end: auto-generated types

	def _post(self, cmd):
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
		except Exception as e:
			frappe.throw(_("Connectivity issue with whatsmeow server: {}").format(e))
		if res.status_code != 200:
			return
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


def send_whatsapp(msg, recipients=None):
	settings = frappe.get_single("WhatsApp Settings")

	if not settings.jid:
		frappe.throw(_("WhatsApp currently not linked: please revise WhatsApp Settings"))

	for recp in recipients:
		settings._post({"cmd": "send", "args": [recp, msg]})
