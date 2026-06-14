# Copyright (c) 2026, Sowaan and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CloudSubscription(Document):
	pass


# ── Rate-limit constants ───────────────────────────────────────────────────────
_RL_MAX_REQUESTS = 5      # max submissions per IP
_RL_WINDOW_SEC   = 3600   # within this many seconds (1 hour)


def _get_client_ip():
	"""Return the real client IP, respecting X-Forwarded-For from a trusted proxy."""
	environ = frappe.local.request.environ
	forwarded_for = environ.get("HTTP_X_FORWARDED_FOR", "")
	if forwarded_for:
		return forwarded_for.split(",")[0].strip()
	return environ.get("REMOTE_ADDR", "unknown")


def _check_rate_limit():
	"""
	Allow at most _RL_MAX_REQUESTS from a single IP within _RL_WINDOW_SEC.
	Uses Redis INCR + EXPIRE for an atomic, fixed-window counter.
	Silently passes if Redis is unreachable so a cache outage never blocks signups.
	"""
	ip  = _get_client_ip()
	key = f"cloud_sub_rl:{ip}"

	try:
		redis = frappe.cache()
		count = redis.incr(key)          # atomic increment; creates key at 0 if missing
		if count == 1:
			redis.expire(key, _RL_WINDOW_SEC)   # set TTL only on first hit in window
	except Exception:
		return   # Redis unavailable — fail open rather than block legitimate users

	if count > _RL_MAX_REQUESTS:
		frappe.local.response["http_status_code"] = 429
		frappe.throw(
			"Too many requests from your IP address. Please wait an hour and try again.",
			title="Rate Limit Exceeded",
		)


# ── Public guest endpoint ──────────────────────────────────────────────────────

@frappe.whitelist(allow_guest=True)
def get_packages():
	"""Return all Cloud Package records for the public onboarding form."""
	try:
		# price / users_limit are new fields — only available after bench migrate
		pkgs = frappe.get_all(
			"Cloud Package",
			fields=["name", "title", "price", "users_limit", "description"],
			order_by="creation asc",
		)
	except Exception:
		# Columns don't exist yet — return without them; frontend fallback fills the gap
		pkgs = frappe.get_all(
			"Cloud Package",
			fields=["name", "title", "description"],
			order_by="creation asc",
		)
	return pkgs


@frappe.whitelist()
def get_default_site_suffix():
	return frappe.db.get_single_value("Cloud Settings", "site_suffix")


@frappe.whitelist(allow_guest=True)
def create_subscription(
	company_name,
	abbr,
	instance_name,
	user_email,
	user_password,
	selected_package,
	country="Saudi Arabia",
	hp="",
):
	"""Public endpoint for the onboarding form — no login required."""

	# ── Layer 1: honeypot ─────────────────────────────────────────────────────
	if hp:
		return {"name": "pending", "status": "Draft"}

	# ── Layer 2: rate limit ───────────────────────────────────────────────────
	_check_rate_limit()

	# ── Layer 3: field validation ─────────────────────────────────────────────
	required = {
		"Company Name": company_name,
		"Abbreviation": abbr,
		"Instance Name": instance_name,
		"Email": user_email,
		"Password": user_password,
		"Package": selected_package,
	}
	for label, value in required.items():
		if not value or not str(value).strip():
			frappe.throw(f"{label} is required", frappe.MandatoryError)

	if len(user_password) < 8:
		frappe.throw("Password must be at least 8 characters.")

	# ── Layer 4: duplicate checks ─────────────────────────────────────────────
	if frappe.db.exists("Cloud Subscription", {"company_name": company_name}):
		frappe.throw(f'A subscription for "{company_name}" already exists.')

	if frappe.db.exists("Cloud Subscription", {"instance_name": instance_name}):
		frappe.throw(f'Instance name "{instance_name}" is already taken.')

	if not frappe.db.exists("Cloud Package", selected_package):
		frappe.throw(f'Package "{selected_package}" does not exist.')

	# ── Create ────────────────────────────────────────────────────────────────
	doc = frappe.get_doc({
		"doctype": "Cloud Subscription",
		"company_name": company_name,
		"abbr": abbr,
		"instance_name": instance_name,
		"user_email": user_email,
		"user_password": user_password,
		"selected_package": selected_package,
		"country": country,
		"currency": "SAR",        # always SAR — not user-controlled
		"status": "Provisioning",
		"provisioning_logs": "",
	})
	doc.insert(ignore_permissions=True)
	frappe.db.commit()

	frappe.enqueue(
		"sowaan_cloud.utils.provision.provision_from_subscription",
		queue="long",
		docname=doc.name,
		timeout=3600,
		is_async=True,
	)

	return {"name": doc.name, "status": doc.status}


@frappe.whitelist(allow_guest=True)
def get_subscription_status(name):
	"""Poll endpoint for the frontend to track async provisioning progress."""
	try:
		doc = frappe.get_doc("Cloud Subscription", name)
	except frappe.DoesNotExistError:
		frappe.throw("Subscription not found.", frappe.DoesNotExistError)

	return {
		"status": doc.status,
		"provisioning_step": doc.provisioning_step,
		"site_name": doc.site_name,
		"error": doc.provisioning_logs if doc.status == "Failed" else None,
	}
