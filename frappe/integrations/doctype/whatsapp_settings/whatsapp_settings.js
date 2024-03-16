// Copyright (c) 2024, Frappe Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("WhatsApp Settings", {
	refresh(frm) {
		if (!frm.doc.jid) {
			frm.add_custom_button(__("Request QR code"), () => {
				frm.dashboard.set_headline(__("Generating QR..."));
				frm.call("pair").then((r) => {
					let qr = r.message;
					frm.dashboard.set_headline("");
					if (qr) {
						let template =
							'<div class="clearfix"><p><div class="float-left"><h3>In WhatsApp ...</h3><ol> <li>Tab on "&vellip;"</li> <li>Tab on "Linked devices"</li> <li>Tab on "Link a device"</li> <li>Scan this code</li> <li>Wait for the time to elapse</li></ol><progress value="0" max="60" id="progressBar"></progress></div><img src="' +
							qr +
							'" class="img-thumbnail h-25 w-auto float-right"/></p></div>';
						frm.dashboard.set_headline_alert(
							frappe.render_template(template),
							"yellow"
						);
						var timeleft = 60;
						var waitTimer = setInterval(function () {
							frm.call("whoami").then((r) => {
								if (r.message != []) {
									clearInterval(waitTimer);
									frm.dashboard.set_headline("");
									frm.reload_doc();
								}
							});
							if (timeleft <= 0) {
								clearInterval(waitTimer);
								frm.dashboard.set_headline("");
								frm.reload_doc();
							}
							document.getElementById("progressBar").value = 60 - timeleft;
							timeleft -= 5;
						}, 5000);
					} else {
						frm.dashboard.set_headline(__("Generation failed."));
						clearInterval(waitTimer);
						setTimeout(() => {
							frm.dashboard.set_headline("");
						}, 3000);
					}
				});
			});
		} else {
			frm.toggle_display(["jid"], true);
			frm.add_custom_button(__("Logout from WhatsApp"), () => {
				frm.call("logout").then(() => {
					frm.reload_doc();
				});
			});
		}
	},
});
