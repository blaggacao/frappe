# Copyright (c) 2024, Frappe Technologies and contributors
# For license information, please see license.txt
import asyncio
import json
import os
from contextlib import closing

from nio import (
	AsyncClient,
	AsyncClientConfig,
	DirectRoomsErrorResponse,
	DiscoveryInfoResponse,
	JoinedMembersError,
	LoginResponse,
)

import frappe
from frappe import _
from frappe.model.document import Document

DEVICE_NAME = "frappe"


class MatrixSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		oauth_client: DF.Link | None
		server_url: DF.Data
	# end: auto-generated types

	async def connect(self, user):
		client_config = AsyncClientConfig(
			max_limit_exceeded=0,
			max_timeouts=5,
			# store_sync_tokens=True,
			# encryption_enabled=True,
		)

		client = AsyncClient(
			self.server_url,
			config=client_config,
			# during testing with self-signed certs
			# ssl=False,
		)
		response = await client.discovery_info()
		if isinstance(response, DiscoveryInfoResponse):
			client.homeserver = response.homeserver_url
		else:
			self.log_error(f"Failed to discover matrix server on {self.server_url}: {response}")

		local_store_path = frappe.get_site_path("matrix")

		if not os.path.exists(local_store_path):
			os.mkdir(local_store_path)

		local_store_user_file = os.path.join(local_store_path, user)

		if not os.path.exists(local_store_user_file):
			# https://matrix-org.github.io/synapse/latest/jwt.html
			from authlib.jose import jwt

			config = frappe.get_doc("OAuth Client", self.oauth_client)
			jwt_res = jwt.encode(
				{"alg": "HS256"},
				{"sub": user.lstrip("@").split(":")[0]},
				config.client_secret,
			)
			resp = await client.login_raw(
				{
					"type": "org.matrix.login.jwt",
					"token": jwt_res.decode("ascii"),
					"initial_device_display_name": DEVICE_NAME,
				}
			)
			# check that we logged in successfully
			if isinstance(resp, LoginResponse):
				with open(local_store_user_file, "w") as f:
					json.dump(
						{
							"user_id": resp.user_id,
							"device_id": resp.device_id,
							"access_token": resp.access_token,
						},
						f,
					)
			else:
				self.log_error(f"Failed to log in user {user}: {resp}")

		else:
			with open(local_store_user_file) as f:
				contents = f.read()
			config = json.loads(contents)
			client.restore_login(**config)

		return client

	async def send(self, client, room_id, message, formatted_message):
		await client.room_send(
			room_id,
			message_type="m.room.message",
			content={
				"msgtype": "m.text",
				"body": message,
				"format": "org.matrix.custom.html",
				"formatted_body": formatted_message,
			},
		)

	async def send_dm(self, client, recipient, message, formatted_message):
		resp = await client.list_direct_rooms()
		if isinstance(resp, DirectRoomsErrorResponse):
			self.log_error(f"Unable to list joined rooms for user {client.user_id}: {resp}")
			return
		recv_room = None
		for recv, rooms in resp.rooms.items():
			if recipient == recv:
				recv_room = rooms[0]
				break
		if recipient == client.user_id:
			self.log_error(f"Unable to send message to oneself for {client.user_id}")
			return
		if not recv_room:
			self.log_error(f"Unable to find a DM with {recipient} for {client.user_id}")
			return
		await client.room_send(
			recv_room,
			message_type="m.room.message",
			content={
				"msgtype": "m.text",
				"body": message,
				"format": "org.matrix.custom.html",
				"formatted_body": formatted_message,
			},
		)


@frappe.whitelist()
def send_matrix(msg, formatted_msg, user, recipients=None, room_id=None):
	matrix = frappe.get_single("Matrix Settings")

	async def _send_matix():
		tasks = set()
		client = await matrix.connect(user)
		try:
			for recp in recipients:
				tasks.add(asyncio.create_task(matrix.send_dm(client, recp, msg, formatted_msg)))
			if room_id:
				tasks.add(asyncio.create_task(matrix.send(client, room_id, msg, formatted_msg)))
			await asyncio.gather(*tasks)
		except (asyncio.CancelledError, KeyboardInterrupt):
			await client.close()

	asyncio.run(_send_matix())
