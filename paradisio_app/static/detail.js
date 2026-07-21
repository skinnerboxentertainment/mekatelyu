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

    var amToggle = document.querySelector("[data-amenities-toggle]");
    var amSection = document.querySelector("[data-amenities-section]");
    if (amToggle && amSection) {
        amToggle.addEventListener("click", function () {
            var expanded = amSection.classList.toggle("expanded");
            amToggle.textContent = expanded ? "Show less" : "View all " + amSection.querySelectorAll(".amenity-chip").length + " amenities";
        });
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
})();
