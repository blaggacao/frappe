# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

# Database Module
# --------------------
from shutil import which

from frappe.database.database import savepoint


def setup_database(
	force, source_sql=None, verbose=None, socket=None, host=None, port=None, user=None, password=None
):
	import frappe

	if frappe.conf.db_type == "postgres":
		import frappe.database.postgres.setup_db

		return frappe.database.postgres.setup_db.setup_database(
			force, source_sql, verbose, socket, host, port, user, password
		)
	else:
		import frappe.database.mariadb.setup_db

		return frappe.database.mariadb.setup_db.setup_database(
			force, source_sql, verbose, socket, host, port, user, password
		)


def drop_user_and_database(db_name, socket=None, host=None, port=None, user=None, password=None):
	import frappe

	if frappe.conf.db_type == "postgres":
		import frappe.database.postgres.setup_db

		return frappe.database.postgres.setup_db.drop_user_and_database(
			db_name, socket, host, port, user, password
		)
	else:
		import frappe.database.mariadb.setup_db

		return frappe.database.mariadb.setup_db.drop_user_and_database(
			db_name, socket, host, port, user, password
		)


def get_db(socket=None, host=None, user=None, password=None, port=None, dbname=None):
	import frappe

	if frappe.conf.db_type == "postgres":
		import frappe.database.postgres.database

		return frappe.database.postgres.database.PostgresDatabase(
			socket, host, user, password, port, dbname
		)
	else:
		import frappe.database.mariadb.database

		return frappe.database.mariadb.database.MariaDBDatabase(
			socket, host, user, password, port, dbname
		)


def get_command(
	socket=None, host=None, port=None, user=None, password=None, db_name=None, extra=None, dump=False
):
	import frappe

	if frappe.conf.db_type == "postgres":
		if dump:
			bin, bin_name = which("pg_dump"), "pg_dump"
		else:
			bin, bin_name = which("psql"), "psql"

		host = frappe.utils.esc(host, "$ ")
		user = frappe.utils.esc(user, "$ ")
		db_name = frappe.utils.esc(db_name, "$ ")

		conn_string = str
		if socket and password:
			conn_string = f"postgresql://{user}:{password}@/{db_name}?host={socket}"
		elif socket:
			conn_string = f"postgresql://{user}@/{db_name}?host={socket}"
		elif password:
			password = frappe.utils.esc(password, "$ ")
			conn_string = f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
		else:
			conn_string = f"postgresql://{user}@{host}:{port}/{db_name}"

		command = [conn_string]

		if extra:
			command.extend(extra)

	else:
		if dump:
			bin, bin_name = which("mariadb-dump") or which("mysqldump"), "mariadb-dump"
		else:
			bin, bin_name = which("mariadb") or which("mysql"), "mariadb"

		user = frappe.utils.esc(user, "$ ")
		db_name = frappe.utils.esc(db_name, "$ ")

		command = [f"--user={user}"]
		if socket:
			socket = frappe.utils.esc(socket, "$ ")
			command.append(f"--socket={socket}")
		elif host and port:
			host = frappe.utils.esc(host, "$ ")
			command.append(f"--host={host}")
			command.append(f"--port={port}")

		if password:
			password = frappe.utils.esc(password, "$ ")
			command.append(f"--password={password}")

		if dump:
			command.extend(
				[
					"--single-transaction",
					"--quick",
					"--lock-tables=false",
				]
			)
		else:
			command.extend(
				[
					"--pager='less -SFX'",
					"--safe-updates",
					"--no-auto-rehash",
				]
			)

		command.append(db_name)

		if extra:
			command.extend(extra)

	return bin, command, bin_name
