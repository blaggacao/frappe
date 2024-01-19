// website_script.js
{% if javascript -%}{{ javascript }}{%- endif %}

{% if google_analytics_id -%}
// Google Analytics
(function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
(i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
})(window,document,'script','//www.google-analytics.com/analytics.js','ga');

ga('create', '{{ google_analytics_id }}', 'auto');
{% if google_analytics_anonymize_ip %}
ga('set', 'anonymizeIp', true);
{% endif %}
ga('send', 'pageview');
// End Google Analytics
{%- endif %}

{% if enable_view_tracking %}

	window.frappe.track = (event_name) => { // TODO: add similar, optimized utility to frappe/builder
 		if (navigator.doNotTrack == 1 || window.is_404) {
			return
		};

    function getMetaTags() {
      const m = {},
          tt = document.getElementsByTagName('meta');
      tt.forEach(t => {
          const [k, v] = ((t.getAttribute('name') || t.getAttribute('property') || t.getAttribute('http-equiv')), t.getAttribute('content'));
          m[k] = v
      });
      return m
    }


    let b = frappe.utils.get_browser(),
        q = frappe.utils.get_query_params(),
        c = frappe.get_cookies(),
        m = getMetaTags();
		// Get visitor ID based on browser uniqueness
		import('https://openfpcdn.io/fingerprintjs/v3')
			.then(fingerprint_js => fingerprint_js.load())
			.then(fp => fp.get())
			.then(result => {
				frappe.call("frappe.website.log_event", {
					event_name: event_name,
					referrer: document.referrer,
					browser: b.name,
					version: b.version,
					user_tz: Intl.DateTimeFormat().resolvedOptions().timeZone,
					source: q.source || q.utm_source,
					medium: q.medium || q.utm_medium,
					campaign: q.campaign || q.utm_campaign,
					content: q.content || q.utm_content,
					visitor_id: result.visitorId,
	{%- if tracking_data_capture_js -%}
          data: function() {
              {{ tracking_data_capture_js }}
              return r
          }
	{%- endif -%}
				})
		})
	};

	frappe.ready(() => frappe.track("WebPageView"));
{% endif %}
