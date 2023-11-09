import os

import frappe
from frappe import _


def setup_database(force, source_sql, verbose, socket, host, port, user, password):
	root_conn = get_root_connection(socket, host, port, user, password)
	root_conn.commit()
	root_conn.sql("end")
	root_conn.sql(f"DROP DATABASE IF EXISTS `{frappe.conf.db_name}`")
	root_conn.sql(f"DROP USER IF EXISTS {frappe.conf.db_name}")
	root_conn.sql(f"CREATE DATABASE `{frappe.conf.db_name}`")
	root_conn.sql(f"CREATE user {frappe.conf.db_name} password '{frappe.conf.db_password}'")
	root_conn.sql("GRANT ALL PRIVILEGES ON DATABASE `{0}` TO {0}".format(frappe.conf.db_name))
	root_conn.close()

	bootstrap_database(frappe.conf.db_name, verbose, source_sql=source_sql)
	frappe.connect()


def bootstrap_database(db_name, verbose, source_sql=None):
	frappe.connect(db_name=db_name)
	import_db_from_sql(source_sql, verbose)
	frappe.connect(db_name=db_name)

	if "tabDefaultValue" not in frappe.db.get_tables():
		import sys

		from click import secho

		secho(
			"Table 'tabDefaultValue' missing in the restored site. "
			"This may be due to incorrect permissions or the result of a restore from a bad backup file. "
			"Database not installed correctly.",
			fg="red",
		)
		sys.exit(1)


def import_db_from_sql(source_sql=None, verbose=False):
	from shutil import which

	from frappe.database import get_command
	from frappe.utils import execute_in_shell

	# bootstrap db
	if not source_sql:
		source_sql = os.path.join(os.path.dirname(__file__), "framework_postgres.sql")

	pv = which("pv")

	command = []

	if pv:
		command.extend([f"{pv}", f"{source_sql}", "|"])
		source = []
		print("Restoring Database file...")
	else:
		source = ["-f", f"{source_sql}"]

	bin, args, bin_name = get_command(
		socket=frappe.conf.db_socket,
		host=frappe.conf.db_host,
		port=frappe.conf.db_port,
		user=frappe.conf.db_name,
		password=frappe.conf.db_password,
		db_name=frappe.conf.db_name,
	)

	if not bin:
		frappe.throw(
			_("{} not found in PATH! This is required to restore the database.").format(bin_name),
			exc=frappe.ExecutableNotFound,
		)
	command.append(bin)
	command.extend(args)
	command.extend(source)
	execute_in_shell(" ".join(command), check_exit_code=True, verbose=verbose)
	frappe.cache.delete_keys("")  # Delete all keys associated with this site.


def get_root_connection(socket, host, port, user, password):
	if not frappe.local.flags.root_connection:
		from getpass import getpass, getuser

		if not user:
			user = frappe.conf.get("root_login") or getuser()

		if not password:
			password = frappe.conf.get("root_password")

		if not password and not socket:
			password = getpass("Postgres super user password: ")

		frappe.local.flags.root_connection = frappe.database.get_db(
			socket=socket,
			host=host,
			port=port,
			user=user,
			password=password,
			dbname=user,
		)

	return frappe.local.flags.root_connection


def drop_user_and_database(db_name, socket, host, port, user, password):
	root_conn = get_root_connection(socket, host, port, user, password)
	root_conn.commit()
	root_conn.sql(
		"SELECT pg_terminate_backend (pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = %s",
		(db_name,),
	)
	root_conn.sql("end")
	root_conn.sql(f"DROP DATABASE IF EXISTS {db_name}")
	root_conn.sql(f"DROP USER IF EXISTS {db_name}")
