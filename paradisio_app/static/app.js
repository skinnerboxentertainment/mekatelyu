(function () {
    var PAGE_SIZE = 50;
    var filtered = [];
    var displayCount = PAGE_SIZE;
    var currentView = "list";
    var map = null;
    var markers = null;
    var allMarkers = [];
    var activeIntent = "";
    var CATEGORY_LABELS = {
        hostel: "Hostel", hotel: "Hotel", nightlife: "Nightlife",
        real_estate: "Real estate", restaurant: "Restaurant", services: "Services",
        shopping: "Shopping", tour_company: "Tours", transport: "Transport",
        vacation_rental: "Vacation rental", wellness: "Wellness"
    };

    function categoryLabel(value) {
        var key = (value || "").toLowerCase();
        return CATEGORY_LABELS[key] || key.replace(/_/g, " ").replace(/\b\w/g, function (c) { return c.toUpperCase(); });
    }

    var searchInput = document.getElementById("search");
    var catFilter = document.getElementById("category-filter");
    var tagFilter = document.getElementById("tag-filter");
    var areaFilter = document.getElementById("area-filter");
    var channelFilter = document.getElementById("channel-filter");
    var sortFilter = document.getElementById("sort-filter");
    var resultsDiv = document.getElementById("results");
    var statsLine = document.getElementById("stats-line");
    var chipsDiv = document.getElementById("filter-chips");
    var loadMoreDiv = document.getElementById("load-more");
    var mapDiv = document.getElementById("map-container");
    var viewList = document.getElementById("view-list");
    var viewMap = document.getElementById("view-map");

    function populateFilters() {
        catFilter.innerHTML = '<option value="">All Categories</option>';
        Object.keys(CATEGORIES).sort().forEach(function (c) {
            var opt = document.createElement("option");
            opt.value = c;
            opt.textContent = categoryLabel(c) + " (" + CATEGORIES[c] + ")";
            catFilter.appendChild(opt);
        });
        tagFilter.innerHTML = '<option value="">Any type or quality</option>';
        Object.keys(SEMANTIC_FACETS).sort(function (a, b) {
            return (SEMANTIC_LABELS[a] || a).localeCompare(SEMANTIC_LABELS[b] || b);
        }).forEach(function (tag) {
            var opt = document.createElement("option");
            opt.value = tag;
            opt.textContent = (SEMANTIC_LABELS[tag] || categoryLabel(tag)) + " (" + SEMANTIC_FACETS[tag] + ")";
            tagFilter.appendChild(opt);
        });
        areaFilter.innerHTML = '<option value="">All Areas</option>';
        Object.keys(AREAS).sort().forEach(function (a) {
            var opt = document.createElement("option");
            opt.value = a;
            opt.textContent = a + " (" + AREAS[a] + ")";
            areaFilter.appendChild(opt);
        });
    }

    function matchBusiness(b) {
        var q = searchInput.value.toLowerCase().trim();
        var cat = catFilter.value;
        var area = areaFilter.value;
        var ch = channelFilter.value;
        var tag = tagFilter.value;

        if (q) {
            var match = b.name.toLowerCase().includes(q);
            match = match || (b.category || "").toLowerCase().includes(q);
            match = match || (b.area || "").toLowerCase().includes(q);
            match = match || (b.description || "").toLowerCase().includes(q);
            match = match || (b.badges || []).some(function (x) { return x.toLowerCase().includes(q); });
            match = match || (b.semantic_tags || []).some(function (x) { return x.toLowerCase().includes(q); });
            match = match || (b.semantic_attributes || []).some(function (x) { return x.toLowerCase().includes(q); });
            match = match || (b.search_synonyms || []).some(function (x) { return x.toLowerCase().includes(q); });
            if (!match) return false;
        }
        if (cat && b.category !== cat) return false;
        if (tag && (b.semantic_tags || []).indexOf(tag) === -1 && (b.semantic_attributes || []).indexOf(tag) === -1) return false;
        if (activeIntent && (b.intents || []).indexOf(activeIntent) === -1) return false;
        if (area && b.area !== area) return false;
        if (ch === "whatsapp" && !b.channels.whatsapp) return false;
        if (ch === "instagram" && !b.channels.instagram) return false;
        if (ch === "phone" && !b.channels.phone) return false;
        if (ch === "website" && !b.channels.website) return false;
        if (ch === "booking" && !b.channels.booking_url) return false;
        if (ch === "maps" && !b.channels.google_maps_cid) return false;
        return true;
    }

    function sortResults(a, b) {
        var s = sortFilter.value;
        if (s === "contactability") return b.scores.contactability - a.scores.contactability;
        if (s === "completeness") return b.scores.completeness - a.scores.completeness;
        return a.name.localeCompare(b.name);
    }

    function esc(s) {
        if (!s) return "";
        var d = document.createElement("div");
        d.textContent = s;
        return d.innerHTML;
    }

    function renderChips() {
        if (!chipsDiv) return;
        var chips = [];
        if (searchInput.value.trim()) {
            chips.push('<span class="filter-chip">Search: ' + esc(searchInput.value.trim()) + ' <span class="chip-close" data-clear="search">&times;</span></span>');
        }
        if (catFilter.value) {
            chips.push('<span class="filter-chip">' + esc(catFilter.options[catFilter.selectedIndex].text.split(" (")[0]) + ' <span class="chip-close" data-clear="category">&times;</span></span>');
        }
        if (tagFilter.value) {
            chips.push('<span class="filter-chip">' + esc(SEMANTIC_LABELS[tagFilter.value] || categoryLabel(tagFilter.value)) + ' <span class="chip-close" data-clear="tag">&times;</span></span>');
        }
        if (activeIntent) {
            var intentNames = { eat: "Eat", stay: "Stay", "things-to-do": "Things to Do", shopping: "Shopping", services: "Services", wellness: "Wellness", nightlife: "Nightlife", transport: "Transport" };
            chips.push('<span class="filter-chip">' + esc(intentNames[activeIntent] || activeIntent) + ' <span class="chip-close" data-clear="intent">&times;</span></span>');
        }
        if (areaFilter.value) {
            chips.push('<span class="filter-chip">' + esc(areaFilter.value) + ' <span class="chip-close" data-clear="area">&times;</span></span>');
        }
        if (channelFilter.value) {
            var label = channelFilter.options[channelFilter.selectedIndex].text;
            chips.push('<span class="filter-chip">' + esc(label) + ' <span class="chip-close" data-clear="channel">&times;</span></span>');
        }
        if (chips.length) chips.push('<span class="filter-chip clear-all" id="clear-all-filters">Clear all</span>');
        chipsDiv.innerHTML = chips.join("");

        document.querySelectorAll("[data-clear]").forEach(function (el) {
            el.addEventListener("click", function (e) {
                e.stopPropagation();
                var field = this.getAttribute("data-clear");
                if (field === "search") { searchInput.value = ""; resetAndRender(); return; }
                if (field === "intent") { activeIntent = ""; resetAndRender(); return; }
                var target = field === "category" ? catFilter : field === "tag" ? tagFilter : field === "area" ? areaFilter : channelFilter;
                if (target) { target.value = ""; target.dispatchEvent(new Event("change")); }
            });
        });
        var clearAll = document.getElementById("clear-all-filters");
        if (clearAll) {
            clearAll.addEventListener("click", function () {
                searchInput.value = ""; catFilter.value = ""; tagFilter.value = ""; areaFilter.value = ""; channelFilter.value = ""; activeIntent = "";
                displayCount = PAGE_SIZE;
                catFilter.dispatchEvent(new Event("change"));
            });
        }
    }

    function renderCard(b) {
        var badges = (b.badges || []).map(function (x) {
            return '<span class="channel-tag ' + x.toLowerCase().replace(/\s+/g, "-") + '">' + x + "</span>";
        }).join("");

        var rating = "";
        if (b.rating) {
            var full = Math.floor(b.rating);
            var half = b.rating % 1 >= 0.3 ? "&#189;" : "";
            rating = '<div class="card-rating">' + "&#9733;".repeat(full) + half + " " + b.rating + "</div>";
        }

        return '<a href="businesses/' + b.slug + '.html" class="result-card">' +
            '<div class="result-name">' + esc(b.name) + "</div>" +
            rating +
            '<div class="result-meta">' +
            '<span>' + esc(categoryLabel(b.category) || "Other") + "</span>" +
            '<span>' + esc(b.area || "Unknown") + "</span>" +
            (b.distance_km ? '<span>' + b.distance_km + " km</span>" : "") +
            "</div>" +
            (badges ? '<div class="result-channels">' + badges + "</div>" : "") +
            '<div class="result-cta">' + (b.primary_contact && b.primary_contact.type !== "None" ? esc(b.primary_contact.label) : "View details") + " &rarr;</div>" +
            "</a>";
    }

    function renderLoadMore(total) {
        if (!loadMoreDiv) return;
        var remaining = total - displayCount;
        if (remaining <= 0) {
            loadMoreDiv.innerHTML = '<div class="load-more-end">Showing all ' + total + ' results.</div>';
            return;
        }
        var showing = Math.min(displayCount, total);
        loadMoreDiv.innerHTML = '<div class="load-more-bar"><span class="load-more-text">Showing ' + showing + ' of ' + total + '</span><button class="load-more-btn" id="load-more-btn">Load ' + Math.min(remaining, PAGE_SIZE) + ' more (' + remaining + ' remaining)</button></div>';
        document.getElementById("load-more-btn").addEventListener("click", function () {
            displayCount += PAGE_SIZE;
            renderList();
        });
    }

    function renderList() {
        filtered = BUSINESSES.filter(matchBusiness).sort(sortResults);
        var total = filtered.length;

        renderChips();

        if (total === 0) {
            resultsDiv.innerHTML = '<div class="no-results">No businesses match your filters. Try a different search.</div>';
            statsLine.textContent = "0 results";
            if (loadMoreDiv) loadMoreDiv.innerHTML = "";
            return;
        }

        var shown = filtered.slice(0, displayCount);
        var html = shown.map(renderCard).join("");
        resultsDiv.innerHTML = html;
        var hasFilter = searchInput.value.trim() || catFilter.value || tagFilter.value || areaFilter.value || channelFilter.value || activeIntent;
        if (hasFilter) {
            statsLine.innerHTML = Math.min(displayCount, total) + " of " + total + ' results &middot; <a href="#" id="clear-stats" style="color:var(--coral-600);text-decoration:none;">Clear filter</a>';
            var clearStats = document.getElementById("clear-stats");
            if (clearStats) {
                clearStats.addEventListener("click", function (e) {
                    e.preventDefault();
                    searchInput.value = ""; catFilter.value = ""; tagFilter.value = ""; areaFilter.value = ""; channelFilter.value = ""; activeIntent = "";
                    displayCount = PAGE_SIZE;
                    catFilter.dispatchEvent(new Event("change"));
                });
            }
        } else {
            statsLine.textContent = Math.min(displayCount, total) + " of " + total + " results";
        }
        renderLoadMore(total);
    }

    function initMap() {
        if (map) return;
        if (typeof L === "undefined") {
            mapDiv.innerHTML = '<div class="map-unavailable">Map is temporarily unavailable. Use the list to browse businesses.</div>';
            return;
        }
        map = L.map(mapDiv, { zoomControl: true, attributionControl: true }).setView([9.655, -82.753], 13);
        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            maxZoom: 18,
        }).addTo(map);

        markers = L.markerClusterGroup({
            maxClusterRadius: 50,
            spiderfyOnMaxZoom: true,
            showCoverageOnHover: false,
        });

        BUSINESSES.forEach(function (b) {
            if (!b.lat || !b.lng) return;
            var marker = L.marker([parseFloat(b.lat), parseFloat(b.lng)], {
                title: b.name,
            });
            marker.bindPopup(
                '<strong>' + esc(b.name) + '</strong><br>' +
                esc(b.category || "Uncategorized") + " &middot; " + esc(b.area || "Unknown") +
                (b.rating ? "<br>" + "&#9733;".repeat(Math.floor(b.rating)) + (b.rating % 1 >= 0.3 ? "&#189;" : "") + " " + b.rating : "") +
                '<br><a href="businesses/' + b.slug + '.html" target="_blank">View page &rarr;</a>'
            );
            marker._biz = b;
            allMarkers.push(marker);
        });

        markers.addLayers(allMarkers);
        map.addLayer(markers);

        if (allMarkers.length > 0) {
            var group = L.featureGroup(allMarkers);
            map.fitBounds(group.getBounds().pad(0.1));
        }
    }

    function updateMap() {
        if (!map) return;
        markers.clearLayers();
        var shown = BUSINESSES.filter(matchBusiness);
        var visible = allMarkers.filter(function (m) {
            var b = m._biz;
            return shown.indexOf(b) !== -1;
        });
        markers.addLayers(visible);
        if (visible.length > 0) {
            var group = L.featureGroup(visible);
            map.fitBounds(group.getBounds().pad(0.1));
        }
        statsLine.textContent = visible.length + " of " + BUSINESSES.length + " on map";
    }

    function switchView(view) {
        currentView = view;
        if (view === "map") {
            resultsDiv.style.display = "none";
            loadMoreDiv.style.display = "none";
            mapDiv.classList.add("active");
            viewList.classList.remove("active");
            viewMap.classList.add("active");
            viewList.setAttribute("aria-pressed", "false");
            viewMap.setAttribute("aria-pressed", "true");
            initMap();
            setTimeout(function () { map && map.invalidateSize(); }, 100);
            updateMap();
        } else {
            resultsDiv.style.display = "";
            loadMoreDiv.style.display = "";
            mapDiv.classList.remove("active");
            viewList.classList.add("active");
            viewMap.classList.remove("active");
            viewList.setAttribute("aria-pressed", "true");
            viewMap.setAttribute("aria-pressed", "false");
            var total = BUSINESSES.filter(matchBusiness).length;
            renderList();
        }
    }

    function resetAndRender() {
        displayCount = PAGE_SIZE;
        if (currentView === "map") {
            updateMap();
        } else {
            renderList();
        }
    }

    // View toggle
    viewList.addEventListener("click", function () { switchView("list"); });
    viewMap.addEventListener("click", function () { switchView("map"); });

    // Category shortcut tiles
    document.querySelectorAll(".cat-tile").forEach(function (tile) {
        tile.addEventListener("click", function (e) {
            e.preventDefault();
            activeIntent = this.getAttribute("data-category");
            if (catFilter) { catFilter.value = ""; }
            displayCount = PAGE_SIZE;
            catFilter.dispatchEvent(new Event("change"));
            document.querySelector("#results").scrollIntoView({ behavior: "smooth" });
        });
    });

    // Highlight active category tile when filter changes
    function updateActiveTile() {
        var active = catFilter ? catFilter.value : "";
        document.querySelectorAll(".cat-tile").forEach(function (t) {
            var group = t.getAttribute("data-category");
            if (activeIntent && group === activeIntent) {
                t.style.borderColor = "var(--coral-600, #ed744f)";
                t.style.background = "#fff5f0";
            } else {
                t.style.borderColor = "";
                t.style.background = "";
            }
        });
    }
    catFilter.addEventListener("change", updateActiveTile);
    updateActiveTile();

    searchInput.addEventListener("input", resetAndRender);
    catFilter.addEventListener("change", resetAndRender);
    tagFilter.addEventListener("change", resetAndRender);
    areaFilter.addEventListener("change", resetAndRender);
    channelFilter.addEventListener("change", resetAndRender);
    sortFilter.addEventListener("change", resetAndRender);

    populateFilters();
    renderList();

    // Recalc map size on orientation change
    window.addEventListener("resize", function () {
        if (currentView === "map" && map) {
            map.invalidateSize();
        }
    });
})();
