(function () {
    var mapDiv = document.querySelector("[data-business-map]");
    if (mapDiv) {
        if (typeof L === "undefined") {
            mapDiv.innerHTML = '<p class="map-unavailable">Map is temporarily unavailable. Use the Google Maps link below.</p>';
        } else {
            var lat = Number(mapDiv.getAttribute("data-lat"));
            var lng = Number(mapDiv.getAttribute("data-lng"));
            if (!Number.isFinite(lat) || !Number.isFinite(lng)) {
                mapDiv.innerHTML = '<p class="map-unavailable">Location coordinates are unavailable.</p>';
            } else {
                var map = L.map(mapDiv, { zoomControl: false, attributionControl: false }).setView([lat, lng], 15);
                L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png").addTo(map);
                var pinIcon = L.divIcon({
                    html: '<svg width="28" height="40" viewBox="0 0 28 40" xmlns="http://www.w3.org/2000/svg"><path d="M14 0C6.3 0 0 6.3 0 14c0 10.5 14 26 14 26s14-15.5 14-26C28 6.3 21.7 0 14 0zm0 20a6 6 0 110-12 6 6 0 010 12z" fill="#1a5e3e"/><circle cx="14" cy="14" r="4" fill="#fff"/></svg>',
                    className: "",
                    iconSize: [28, 40],
                    iconAnchor: [14, 40],
                });
                L.marker([lat, lng], { icon: pinIcon }).addTo(map);
            }
        }
    }

    var sheet = document.querySelector("[data-share-sheet]");
    var qrPanel = document.querySelector("[data-share-qr-panel]");
    var triggers = document.querySelectorAll("[data-share-trigger]");

    function toggleSheet(e) {
        if (e) e.stopPropagation();
        if (!sheet) return;
        var open = sheet.hidden;
        sheet.hidden = !open;
        if (qrPanel) qrPanel.hidden = true;
        triggers.forEach(function (t) { t.setAttribute("aria-expanded", String(open)); });
    }

    triggers.forEach(function (t) { t.addEventListener("click", toggleSheet); });

    var closeBtn = document.querySelector("[data-share-close]");
    if (closeBtn) closeBtn.addEventListener("click", toggleSheet);

    document.addEventListener("click", function (e) {
        if (sheet && !sheet.hidden && !sheet.contains(e.target) && !e.target.closest("[data-share-trigger]")) {
            sheet.hidden = true;
            if (qrPanel) qrPanel.hidden = true;
            triggers.forEach(function (t) { t.setAttribute("aria-expanded", "false"); });
        }
    });

    var copyBtn = document.querySelector("[data-share-copy]");
    if (copyBtn) {
        copyBtn.addEventListener("click", function () {
            if (navigator.clipboard) {
                navigator.clipboard.writeText(window.location.href).then(function () {
                    copyBtn.textContent = "Link copied!";
                    setTimeout(function () { copyBtn.textContent = "Copy link"; }, 2000);
                });
            } else {
                copyBtn.textContent = "Copy failed";
            }
        });
    }

    var qrToggle = document.querySelector("[data-share-toggle-qr]");
    if (qrToggle) {
        qrToggle.addEventListener("click", function () {
            if (qrPanel) qrPanel.hidden = !qrPanel.hidden;
        });
    }

    var waLink = document.querySelector("[data-share-wa]");
    if (waLink) {
        waLink.href = "https://wa.me/?text=" + encodeURIComponent(document.title + "\n" + window.location.href);
    }

    var addrCopy = document.querySelector("[data-addr-copy]");
    if (addrCopy) {
        addrCopy.addEventListener("click", function () {
            var text = addrCopy.previousElementSibling ? addrCopy.previousElementSibling.textContent.replace(/^\uD83D\uDCCD\s*/, "") : "";
            if (navigator.clipboard) {
                navigator.clipboard.writeText(text).then(function () {
                    addrCopy.textContent = "Copied!";
                    setTimeout(function () { addrCopy.textContent = "Copy"; }, 2000);
                });
            }
        });
    }

    // Details disclosure: toggle the section state so the summary chips hide
    // while expanded, and return focus to the control + scroll back to the
    // Details heading when the user collapses a long section.
    var detailsEl = document.querySelector(".details-disclosure");
    if (detailsEl) {
        var section = detailsEl.closest(".attributes-section");
        var heading = document.getElementById("details-heading");
        var prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
        detailsEl.addEventListener("toggle", function () {
            if (section) {
                section.classList.toggle("is-expanded", detailsEl.open);
            }
            if (!detailsEl.open) {
                var summary = detailsEl.querySelector("summary");
                if (summary && section) {
                    summary.focus({ preventScroll: true });
                    var target = heading || section;
                    target.scrollIntoView({ behavior: prefersReducedMotion ? "auto" : "smooth", block: "start" });
                }
            }
        });
    }

    // --- Open-now badge (bulletproof client-side time) ---
    // Computes the current date/time in the business's timezone using Intl with
    // an explicit timeZone (immune to the visitor's device timezone), syncs the
    // clock against the server's Date header when possible (immune to wrong
    // device clocks), and handles overnight schedules. On staleness or
    // uncertainty it demotes the claim to "Hours as listed".
    var hoursSection = document.querySelector(".hours-section");
    if (hoursSection) {
        var payload = (function () {
            try { return JSON.parse(hoursSection.getAttribute("data-hours-payload")); }
            catch (e) { return null; }
        })();
        var badge = hoursSection.querySelector("[data-hours-opennow]");
        if (payload && badge) {
            var WEEKDAYS = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"];
            var timezone = payload.timezone || "America/Costa_Rica";
            var capturedAt = payload.capturedAt ? new Date(payload.capturedAt) : null;
            var weekly = payload.weekly || {};

            // Resolve "now" as { dayIndex (0=Sunday), minutes } in the target TZ.
            function nowInTimezone(instant, tz) {
                var parts = new Intl.DateTimeFormat("en-US", {
                    timeZone: tz,
                    weekday: "short",
                    hour: "2-digit",
                    minute: "2-digit",
                    hour12: false,
                }).formatToParts(instant);
                var get = function (type) {
                    var p = parts.filter(function (x) { return x.type === type; })[0];
                    return p ? p.value : "";
                };
                // Intl weekday:"short" yields "Sun"/"Mon"; normalize to WEEKDAYS keys.
                var SHORT_DAYS = ["sun", "mon", "tue", "wed", "thu", "fri", "sat"];
                var dow = get("weekday").toLowerCase().slice(0, 3);
                var dayIndex = SHORT_DAYS.indexOf(dow);
                var hour = parseInt(get("hour"), 10) % 24; // guard "24"
                var minute = parseInt(get("minute"), 10);
                if (isNaN(hour) || isNaN(minute) || dayIndex < 0) return null;
                return { dayIndex: dayIndex, minutes: hour * 60 + minute };
            }

            function toMinutes(t) {
                var m = String(t || "").match(/^(\d{1,2}):(\d{2})$/);
                if (!m) return null;
                return parseInt(m[1], 10) * 60 + parseInt(m[2], 10);
            }

            function isOpenAt(dayIndex, minutes) {
                // Check today's schedule plus the prior day's overnight periods.
                var today = weekly[WEEKDAYS[dayIndex]];
                var yesterday = weekly[WEEKDAYS[(dayIndex + 6) % 7]];

                // Yesterday's overnight period spills into today (minutes < closes).
                if (yesterday && !yesterday.closed) {
                    if (yesterday.open24Hours) return true;
                    var yp = yesterday.periods || [];
                    for (var k = 0; k < yp.length; k++) {
                        if (yp[k].closesNextDay) {
                            var yc = toMinutes(yp[k].closes);
                            if (yc !== null && minutes < yc) return true;
                        }
                    }
                }

                // Today's own schedule.
                if (!today || today.closed) return false;
                if (today.open24Hours) return true;
                var periods = today.periods || [];
                for (var j = 0; j < periods.length; j++) {
                    var p = periods[j];
                    var opens = toMinutes(p.opens);
                    var closes = toMinutes(p.closes);
                    if (opens === null || closes === null) continue;
                    if (p.closesNextDay) {
                        // open from opens until midnight (then handled by next day)
                        if (minutes >= opens) return true;
                    } else if (minutes >= opens && minutes < closes) {
                        return true;
                    }
                }
                return false;
            }

            function fmtClock(t) {
                var m = String(t || "").match(/^(\d{1,2}):(\d{2})$/);
                if (!m) return "";
                var h = parseInt(m[1], 10) % 24;
                var min = m[2];
                var suffix = h < 12 ? "AM" : "PM";
                var hh = h % 12;
                if (hh === 0) hh = 12;
                return hh + ":" + min + " " + suffix;
            }

            // Build the current status text for a given day/time. Returns null
            // when today is not listed (no claim). Never emits a dangling sep.
            function computeStatus(dayIndex, minutes) {
                var today = weekly[WEEKDAYS[dayIndex]];
                var yesterday = weekly[WEEKDAYS[(dayIndex + 6) % 7]];
                if (!today) return { text: "Hours unavailable today", open: false };
                if (today.closed) return { text: "Closed today", open: false };
                if (today.open24Hours) return { text: "Open 24 hours", open: true };

                var periods = today.periods || [];
                var open = isOpenAt(dayIndex, minutes);
                if (open) {
                    // Open due to yesterday's overnight spillover?
                    if (yesterday && !yesterday.closed) {
                        for (var y = 0; y < (yesterday.periods || []).length; y++) {
                            var yp = yesterday.periods[y];
                            var yc = toMinutes(yp.closes);
                            if (yp.closesNextDay && yc !== null && minutes < yc) {
                                return { text: "Open · Closes today at " + fmtClock(yp.closes), open: true };
                            }
                        }
                    }
                    // Find the active period's close time.
                    var closeText = "";
                    for (var i = 0; i < periods.length; i++) {
                        var o = toMinutes(periods[i].opens);
                        var c = toMinutes(periods[i].closes);
                        if (o === null || c === null) continue;
                        var openNow = periods[i].closesNextDay ? minutes >= o : (minutes >= o && minutes < c);
                        if (openNow) {
                            if (periods[i].closesNextDay) closeText = "tomorrow at " + fmtClock(periods[i].closes);
                            else closeText = "at " + fmtClock(periods[i].closes);
                            break;
                        }
                    }
                    return { text: closeText ? "Open · Closes " + closeText : "Open now", open: true };
                }
                // Closed: find today's next opening.
                var nextOpen = "";
                for (var j = 0; j < periods.length; j++) {
                    if (minutes < toMinutes(periods[j].opens)) {
                        nextOpen = "at " + fmtClock(periods[j].opens);
                        break;
                    }
                }
                return { text: nextOpen ? "Closed · Opens " + nextOpen : "Closed", open: false };
            }

            function renderBadge(instant) {
                var now = nowInTimezone(instant, timezone);
                var headerEl = document.querySelector("[data-verified-status]");
                if (!now) {
                    badge.textContent = "Hours as listed";
                    if (headerEl) headerEl.textContent = "Hours as listed";
                    return;
                }
                // Staleness: schedule captured more than 21 days ago.
                var stale = false;
                if (capturedAt && !isNaN(capturedAt.getTime())) {
                    var ageDays = (Date.now() - capturedAt.getTime()) / 86400000;
                    if (ageDays > 21) stale = true;
                }
                if (stale) {
                    badge.textContent = "Hours as listed";
                    if (headerEl) headerEl.textContent = "Hours as listed";
                    return;
                }
                var status = computeStatus(now.dayIndex, now.minutes);
                badge.textContent = status.text;
                if (status.open) badge.classList.remove("is-closed");
                else badge.classList.add("is-closed");
                // Populate the header status placeholder with the same result.
                if (headerEl) {
                    headerEl.textContent = status.text;
                    headerEl.className = status.open ? "biz-open" : "biz-closed";
                }
            }

            // Trusted-clock sync: read the server Date header (same-origin).
            var trusted = null;
            fetch("./favicon.ico", { method: "HEAD", cache: "no-store" })
                .then(function (r) { trusted = r.headers.get("date"); })
                .catch(function () { trusted = null; })
                .then(function () {
                    var tick = function () {
                        if (trusted) {
                            var serverTime = new Date(trusted).getTime();
                            var drift = Date.now() - serverTime;
                            renderBadge(new Date(Date.now() - drift));
                        } else {
                            renderBadge(new Date());
                        }
                    };
                    tick();
                    setInterval(tick, 60000);
                    document.addEventListener("visibilitychange", function () {
                        if (!document.hidden) tick();
                    });
                });
        }
    }
})();
