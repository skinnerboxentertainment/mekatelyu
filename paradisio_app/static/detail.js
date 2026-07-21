(function () {
    var mapDiv = document.querySelector("[data-business-map]");
    if (!mapDiv) return;
    if (typeof L === "undefined") {
        mapDiv.innerHTML = '<p class="map-unavailable">Map is temporarily unavailable. Use the Google Maps link below.</p>';
        return;
    }

    var lat = Number(mapDiv.getAttribute("data-lat"));
    var lng = Number(mapDiv.getAttribute("data-lng"));
    if (!Number.isFinite(lat) || !Number.isFinite(lng)) {
        mapDiv.innerHTML = '<p class="map-unavailable">Location coordinates are unavailable.</p>';
        return;
    }

    var map = L.map(mapDiv, { zoomControl: false, attributionControl: false }).setView([lat, lng], 15);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png").addTo(map);
    L.marker([lat, lng]).addTo(map);
})();
