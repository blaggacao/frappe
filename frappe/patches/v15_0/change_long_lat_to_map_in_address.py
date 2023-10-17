import collections
import json

import frappe
from frappe.geo.utils import convert_to_geojson
from frappe.utils import update_progress_bar


def execute():
	"""On Address: migrate longitude and latitude fields into a location map field"""
	frappe.db.auto_commit_on_many_writes = 1

	fields = ["name", "longitude", "latitude"]

	addresses = frappe.get_all(
		"Address",
		fields=fields,
		filters={"longitude": ("is", "set")},
		as_list=True,
	)
	total = len(addresses)
	Coord = collections.namedtuple("Coord", fields)
	for idx, data in enumerate(addresses):
		c = Coord(*data)
		update_progress_bar("Setting location field for addresses", idx, total)
		frappe.db.set_value(
			"Address",
			c.name,
			"location",
			json.dumps(frappe.geo.utils.convert_to_geojson("coordinates", [c])),
			update_modified=False,
		)
