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

    var shareBtn = document.querySelector("[data-share]");
    if (shareBtn) {
        shareBtn.addEventListener("click", function () {
            var data = {
                title: document.title,
                text: document.querySelector("meta[name='description']")?.content || "",
                url: window.location.href
            };
            if (navigator.share) {
                navigator.share(data).catch(function () {});
            } else {
                navigator.clipboard.writeText(data.url).then(function () {
                    shareBtn.textContent = "Link copied!";
                    setTimeout(function () { shareBtn.textContent = "Share via \u2026"; }, 2000);
                }).catch(function () {
                    shareBtn.textContent = "Copy failed";
                });
            }
        });
    }
})();
