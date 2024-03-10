# Copyright (c) 2024, Frappe Technologies and contributors
# For license information, please see license.txt

import base64
from contextlib import closing
from io import BytesIO

import qrcode
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
from whatsfly import WhatsApp

import frappe
from frappe import _
from frappe.model.document import Document


class WhatsAppSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		is_connected: DF.Check
		title: DF.Data | None
	# end: auto-generated types

	@frappe.whitelist()
	def genreate_qr_code(self):
		input_data = "2@JA1viRxc6z0xApdMhH1IINZ6sbXpmR0iTz/SwCbTKCE5GtUMWcNPKGVZ8B+VlnI9gIlQjLK7OAlaxw==,NjMHcPNw1D2to1yQ7LP/t4SYJs5WyxWLC1hBhLDKPAA=,KpouGfWIzd6+dqdCaEPqXAMFb7kTSlyHKErcTueJh1g=,bwUuHVcoWQ7CI7fj/HMX+G0K/V9MbDoYcKUw6LCli8I="
		qr = qrcode.QRCode(version=7, box_size=6, border=3)
		qr.add_data(input_data)
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
	whatsapp = frappe.get_single("WhatsApp Settings")

	# if not whatsapp.is_connected:
	# 	frappe.throw(_("Please initialize WhatsApp Settings via the device linking QR code"))

	with closing(WhatsApp()) as chat:
		for recp in recipients:
			chat.send_message(phone=recp, message=msg)
