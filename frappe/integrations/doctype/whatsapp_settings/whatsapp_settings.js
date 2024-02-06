// Copyright (c) 2024, Frappe Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("WhatsApp Settings", {
	refresh(frm) {
		frm.add_custom_button(__("Request device linking QR"), () => {
			frm.dashboard.set_headline(__("Generating QR..."));
			frm.call("genreate_qr_code").then((r) => {
				let qr = r.message;
				frm.dashboard.set_headline("");
				if (qr) {
					let template =
						'<div class="clearfix"><p><div class="float-left"><h3>In WhatsApp ...</h3><ol> <li>Tab on "&vellip;"</li> <li>Tab on "Linked devices"</li> <li>Tab on "Link a device"</li> <li>Scan this code</li></ol><progress value="0" max="30" id="progressBar"></progress></div><img src="' +
						qr +
						'" class="img-thumbnail h-25 w-auto float-right"/></p></div>';
					frm.dashboard.set_headline_alert(frappe.render_template(template), "yellow");
					setTimeout(() => {
						frm.dashboard.set_headline("");
					}, 31000);
					var timeleft = 30;
					var waitTimer = setInterval(function () {
						if (timeleft <= 0) {
							clearInterval(waitTimer);
						}
						document.getElementById("progressBar").value = 30 - timeleft;
						timeleft -= 1;
					}, 1000);
				} else {
					frm.dashboard.set_headline(__("Generation failed."));
					setTimeout(() => {
						frm.dashboard.set_headline("");
					}, 3000);
				}
			});
		});
	},
});
