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
                L.marker([lat, lng]).addTo(map);
            }
        }
    }

    var sheet = document.querySelector("[data-share-sheet]");
    var qrBlock = document.querySelector("[data-share-qr]");
    var triggers = document.querySelectorAll("[data-share-trigger]");

    function toggleSheet(e) {
        if (e) e.stopPropagation();
        if (!sheet) return;
        var open = sheet.hidden;
        sheet.hidden = !open;
        if (qrBlock) qrBlock.hidden = true;
        // Re-trigger all trigger buttons
        triggers.forEach(function (t) { t.setAttribute("aria-expanded", String(open)); });
    }

    triggers.forEach(function (t) { t.addEventListener("click", toggleSheet); });

    var closeBtn = document.querySelector("[data-share-close]");
    if (closeBtn) closeBtn.addEventListener("click", toggleSheet);

    document.addEventListener("click", function (e) {
        if (sheet && !sheet.hidden && !sheet.contains(e.target) && !e.target.closest("[data-share-trigger]")) {
            sheet.hidden = true;
            if (qrBlock) qrBlock.hidden = true;
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

    var qrToggle = document.querySelector("[data-share-qr]");
    if (qrToggle) {
        qrToggle.addEventListener("click", function () {
            if (qrBlock) qrBlock.hidden = !qrBlock.hidden;
        });
    }

    var waLink = document.querySelector("[data-share-wa]");
    if (waLink) {
        waLink.href = "https://wa.me/?text=" + encodeURIComponent(document.title + "\n" + window.location.href);
    }
})();
