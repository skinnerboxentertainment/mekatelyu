import html
import json
from pathlib import Path
from urllib.parse import quote


def load_organizations(data_path):
    path = Path(data_path)
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        records = json.load(f)
    orgs = []
    for slug, data in records.items():
        org = {
            "slug": data.get("slug", slug),
            "name": data.get("name", slug),
            "entityType": data.get("entityType", "community_organization"),
            "partnerTier": data.get("partnerTier", ""),
            "partnershipStatus": data.get("partnershipStatus", "proposed"),
            "category": data.get("category", "community_safety"),
            "area": data.get("area", ""),
            "featured": data.get("featured", False),
            "hero": data.get("hero", {}),
            "channels": data.get("channels", {}),
            "emergency": data.get("emergency", {}),
            "impact": data.get("impact", []),
            "programs": data.get("programs", []),
            "team": data.get("team", []),
            "teamPageUrl": data.get("teamPageUrl", ""),
            "relatedPlaces": data.get("relatedPlaces", []),
            "sources": data.get("sources", []),
        }
        orgs.append(org)
    return orgs


def public_org_summary(org):
    return {
        "slug": org["slug"],
        "name": org["name"],
        "category": org["category"],
        "area": org["area"],
        "lat": "",
        "lng": "",
        "distance_km": "",
        "status": "active",
        "channels": {
            "phone": False,
            "whatsapp": False,
            "instagram": False,
            "website": bool(org["channels"].get("website")),
            "booking_url": False,
            "google_maps_cid": False,
        },
        "primary_contact": {"type": "Website", "label": "Visit Website"},
        "scores": {"contactability": 10, "visibility": 10, "completeness": 0},
        "badges": ["Community Safety Partner"],
        "intents": ["community"],
        "discovery_groups": ["community"],
        "semantic_tags": ["community-safety", "nonprofit"],
        "semantic_attributes": [],
        "search_synonyms": ["safety", "lifeguard", "rescue", "beach safety", "emergency"],
        "description": org.get("hero", {}).get("summary", ""),
        "rating": None,
    }


def _hero_html(org):
    hero = org.get("hero", {})
    eyebrow = html.escape(hero.get("eyebrow", ""))
    title = html.escape(hero.get("title", ""))
    tagline = html.escape(hero.get("tagline", ""))
    summary = html.escape(hero.get("summary", ""))
    return f"""
<header class="org-header">
  <div class="org-eyebrow">
    <span class="org-badge">{eyebrow}</span>
  </div>
  <h1 class="org-title">{title}</h1>
  <p class="org-tagline">{tagline}</p>
  <p class="org-summary">{summary}</p>
  <div class="org-actions">
    <a href="{html.escape(org['channels'].get('website', '#'), quote=True)}" class="org-btn org-btn-primary" target="_blank" rel="noopener">Visit Website</a>
    <a href="{html.escape(org['channels'].get('donate', '#'), quote=True)}" class="org-btn org-btn-outline" target="_blank" rel="noopener">Donate</a>
  </div>
</header>"""


def _impact_html(org):
    items = org.get("impact", [])
    if not items:
        return ""
    cards = ""
    for item in items:
        metric = html.escape(item.get("metric", ""))
        label = html.escape(item.get("label", ""))
        attribution = html.escape(item.get("attribution", ""))
        cards += f"""
  <div class="impact-card">
    <div class="impact-metric">{metric}</div>
    <div class="impact-label">{label}</div>
    <div class="impact-attribution">{attribution}</div>
  </div>"""
    return f"""
<section class="org-section org-impact">
  <h2 class="org-section-title">Impact</h2>
  <div class="impact-grid">{cards}
  </div>
</section>"""


def _programs_html(org):
    items = org.get("programs", [])
    if not items:
        return ""
    cards = ""
    for item in items:
        title = html.escape(item.get("title", ""))
        summary = html.escape(item.get("summary", ""))
        schedule = item.get("schedule", "")
        cost = item.get("cost")
        confirm = item.get("confirmWithOrganizer", False)
        meta_parts = []
        if schedule:
            meta_parts.append(f"<span class=\"program-schedule\">{html.escape(schedule)}</span>")
        if cost:
            meta_parts.append(f"<span class=\"program-cost\">{html.escape(cost)}</span>")
        if confirm:
            meta_parts.append("<span class=\"program-confirm\">Confirm with organizer</span>")
        meta_html = " &middot; ".join(meta_parts) if meta_parts else ""
        cards += f"""
  <div class="program-card">
    <h3 class="program-title">{title}</h3>
    {('<div class="program-meta">' + meta_html + '</div>') if meta_html else ''}
    <p class="program-summary">{summary}</p>
  </div>"""
    return f"""
<section class="org-section org-programs">
  <h2 class="org-section-title">Programs</h2>
  <div class="programs-grid">{cards}
  </div>
</section>"""


def _emergency_html(org):
    em = org.get("emergency", {})
    mode = em.get("mode", "pending")
    primary = html.escape(em.get("primaryNumber", "911"))
    disclaimer = html.escape(em.get("disclaimer", ""))
    network_summary = html.escape(em.get("networkSummary", ""))
    demo_instructions = html.escape(em.get("demoInstructions", ""))
    slug = html.escape(org.get("slug", "org"))

    demo_section = ""
    if mode == "demo":
        beaches = ["Playa Grande", "Playa Chiquita", "Punta Uva", "Playa Negra", "Cocles"]
        beach_options = "".join(f"<option value=\"{b}\">{b}</option>" for b in beaches)
        demo_section = f"""
<div class="demo-dispatch">
  <button class="demo-dispatch-toggle" onclick="var p=this.nextElementSibling;var v=p.style.display;p.style.display=v==='none'?'block':'none';this.textContent=v==='none'?'Hide Demo Alert System':'Try Demo Alert System'">
    Try Demo Alert System
  </button>
  <div class="demo-dispatch-panel" style="display:none">
    <p class="demo-dispatch-label">Demo: Simulate an emergency alert to Caribbean Guard's network.</p>
    <div class="demo-form-row">
      <select id="demo-beach-{slug}" class="demo-select" aria-label="Select beach">
        {beach_options}
      </select>
      <button class="demo-send-btn" onclick="
        var btn=this;var status=document.getElementById('demo-status-{slug}');
        var beach=document.getElementById('demo-beach-{slug}').value;
        btn.disabled=true;btn.textContent='Sending...';
        setTimeout(function(){{
          status.style.display='block';
          status.innerHTML='&#10003; Demo alert sent for <strong>'+beach+'</strong>. No real alert was dispatched. This is a demonstration.';
          btn.style.display='none';
        }},1200);
      ">Send Demo Alert</button>
    </div>
    <div id="demo-status-{slug}" class="demo-status" style="display:none"></div>
    <p class="demo-note">{demo_instructions}</p>
  </div>
</div>"""

    return f"""
<section class="org-section org-emergency">
  <div class="emergency-panel">
    <div class="emergency-header">
      <span class="emergency-icon">!</span>
      <h2 class="emergency-title">Water Emergency?</h2>
    </div>
    <ol class="emergency-steps">
      <li><strong>Call {primary}</strong> — give the exact beach or landmark.</li>
      <li>Do not enter dangerous water unless trained and equipped.</li>
    </ol>
    <a href="tel:{primary}" class="emergency-call-btn">Call {primary}</a>
    <p class="emergency-network">{network_summary}</p>
    {demo_section}
    <p class="emergency-disclaimer">{disclaimer}</p>
  </div>
</section>"""


def _team_html(org):
    members = org.get("team", [])
    if not members:
        return ""
    cards = ""
    for m in members:
        name = html.escape(m.get("name", ""))
        role = html.escape(m.get("role", ""))
        bio = html.escape(m.get("bio", ""))
        cards += f"""
  <div class="team-card">
    <div class="team-name">{name}</div>
    <div class="team-role">{role}</div>
    <p class="team-bio">{bio}</p>
  </div>"""
    team_url = html.escape(org.get("teamPageUrl", ""), quote=True)
    return f"""
<section class="org-section org-team">
  <h2 class="org-section-title">Team</h2>
  <div class="team-grid">{cards}
  </div>
  {('<a href="' + team_url + '" class="org-btn org-btn-outline org-btn-small" target="_blank" rel="noopener">View full team &rarr;</a>') if team_url else ''}
</section>"""


def _related_html(org):
    places = org.get("relatedPlaces", [])
    if not places:
        return ""
    items = "".join(f"<li class=\"related-place\">{html.escape(p)}</li>" for p in places)
    return f"""
<section class="org-section org-related">
  <h2 class="org-section-title">Related Beaches</h2>
  <p class="org-section-note">Caribbean Guard operates in the South Caribbean. Check official sources for current patrol information.</p>
  <ul class="related-list">{items}
  </ul>
</section>"""


def _sources_html(org):
    sources = org.get("sources", [])
    if not sources:
        return ""
    items = ""
    for s in sources:
        url = html.escape(s.get("url", ""), quote=True)
        publisher = html.escape(s.get("publisher", ""))
        accessed = html.escape(s.get("accessed", ""))
        supports = s.get("supports", [])
        supports_str = ", ".join(html.escape(x) for x in supports) if supports else ""
        items += f"<li><a href=\"{url}\" target=\"_blank\" rel=\"noopener\">{url}</a> &mdash; {publisher} &mdash; accessed {accessed}{' &mdash; ' + supports_str if supports_str else ''}</li>"
    return f"""
<section class="org-section org-sources">
  <p class="sources-disclaimer">Information compiled from Caribbean Guard's public website. Operational details and schedules may change. Confirm directly with the organization.</p>
  <details class="sources-details">
    <summary class="sources-summary">Source references</summary>
    <ul class="sources-list">{items}
    </ul>
  </details>
</section>"""


def _sticky_bar_html(org):
    parts = []
    parts.append(f"<a href=\"tel:{html.escape(org['emergency'].get('primaryNumber', '911'))}\" class=\"sticky-emergency\">Call 911</a>")
    website = org["channels"].get("website", "")
    if website:
        parts.append(f"<a href=\"{html.escape(website, quote=True)}\" class=\"org-sticky-btn\" target=\"_blank\" rel=\"noopener\">Website</a>")
    donate = org["channels"].get("donate", "")
    if donate:
        parts.append(f"<a href=\"{html.escape(donate, quote=True)}\" class=\"org-sticky-btn\" target=\"_blank\" rel=\"noopener\">Donate</a>")
    parts.append("<button class=\"sticky-share\" onclick=\"if(navigator.share)navigator.share({title:'Caribbean Guard',url:window.location.href});else alert('Share: '+window.location.href)\">Share</button>")
    return f"""<div class=\"org-sticky-bar\">{"".join(parts)}</div>"""


def _page_title(org):
    name = html.escape(org.get("name", "Organization"))
    return f"{name} — Community Safety Partner — Whappin Puerto Viejo"


def render_organization_html(org, *, nav_html_func):
    nav = nav_html_func("directory", depth=1)
    title = _page_title(org)
    slug = html.escape(org["slug"])
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="referrer" content="strict-origin-when-cross-origin">
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data: https://*.tile.openstreetmap.org; connect-src 'self' https://*.tile.openstreetmap.org; object-src 'none'; base-uri 'self'; form-action 'none'; upgrade-insecure-requests">
<link rel="canonical" href="https://www.whappin.com/businesses/{slug}.html">
<link rel="stylesheet" href="../static/community.css">
</head>
<body>
{nav}
<main class="container org-container">
<a href="../index.html" class="back-link">&larr; Directory</a>
{_hero_html(org)}
{_impact_html(org)}
{_emergency_html(org)}
{_programs_html(org)}
{_team_html(org)}
{_related_html(org)}
{_sources_html(org)}
<footer class="footer">
<p><a href="https://github.com/skinnerboxentertainment/mekatelyu/issues/new?template=qa-feedback.md" target="_blank" rel="noopener">Report a problem</a></p>
</footer>
</main>
{_sticky_bar_html(org)}
</body>
</html>"""
