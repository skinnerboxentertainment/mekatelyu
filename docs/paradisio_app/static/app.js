(function () {
    var PAGE_SIZE = 50;
    var filtered = [];
    var displayCount = PAGE_SIZE;
    var searchInput = document.getElementById("search");
    var catFilter = document.getElementById("category-filter");
    var areaFilter = document.getElementById("area-filter");
    var channelFilter = document.getElementById("channel-filter");
    var sortFilter = document.getElementById("sort-filter");
    var resultsDiv = document.getElementById("results");
    var statsLine = document.getElementById("stats-line");
    var chipsDiv = document.getElementById("filter-chips");
    var loadMoreDiv = document.getElementById("load-more");

    function populateFilters() {
        catFilter.innerHTML = '<option value="">All Categories</option>';
        Object.keys(CATEGORIES).sort().forEach(function (c) {
            var opt = document.createElement("option");
            opt.value = c;
            opt.textContent = c.charAt(0).toUpperCase() + c.slice(1) + " (" + CATEGORIES[c] + ")";
            catFilter.appendChild(opt);
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

        if (q) {
            var match = b.name.toLowerCase().includes(q);
            match = match || (b.category || "").toLowerCase().includes(q);
            match = match || (b.area || "").toLowerCase().includes(q);
            match = match || (b.description || "").toLowerCase().includes(q);
            match = match || (b.badges || []).some(function (x) { return x.toLowerCase().includes(q); });
            if (!match) return false;
        }
        if (cat && b.category !== cat) return false;
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
        if (catFilter.value) {
            chips.push('<span class="filter-chip">' + esc(catFilter.options[catFilter.selectedIndex].text.split(" (")[0]) + ' <span class="chip-close" data-clear="category">&times;</span></span>');
        }
        if (areaFilter.value) {
            chips.push('<span class="filter-chip">' + esc(areaFilter.value) + ' <span class="chip-close" data-clear="area">&times;</span></span>');
        }
        if (channelFilter.value) {
            var label = channelFilter.options[channelFilter.selectedIndex].text;
            chips.push('<span class="filter-chip">' + esc(label) + ' <span class="chip-close" data-clear="channel">&times;</span></span>');
        }
        if (chips.length > 1) {
            chips.push('<span class="filter-chip clear-all" id="clear-all-filters">Clear all</span>');
        }
        chipsDiv.innerHTML = chips.join("");

        document.querySelectorAll("[data-clear]").forEach(function (el) {
            el.addEventListener("click", function (e) {
                e.stopPropagation();
                var field = this.getAttribute("data-clear");
                if (field === "category") catFilter.value = "";
                if (field === "area") areaFilter.value = "";
                if (field === "channel") channelFilter.value = "";
                displayCount = PAGE_SIZE;
                render();
            });
        });
        var clearAll = document.getElementById("clear-all-filters");
        if (clearAll) {
            clearAll.addEventListener("click", function () {
                catFilter.value = "";
                areaFilter.value = "";
                channelFilter.value = "";
                displayCount = PAGE_SIZE;
                render();
            });
        }
    }

    function renderCard(b) {
        var badges = (b.badges || []).map(function (x) {
            return '<span class="channel-tag ' + x.toLowerCase().replace(/\s+/g, "-") + '">' + x + "</span>";
        }).join("");

        var scores = "";
        if (b.scores) {
            scores = '<div class="result-scores">' +
                '<span class="score-dot">Contact ' + b.scores.contactability + "</span>" +
                '<span class="score-dot">Visible ' + b.scores.visibility + "</span>" +
                '<span class="score-dot">Complete ' + b.scores.completeness + "</span>" +
                "</div>";
        }

        return '<a href="businesses/' + b.slug + '.html" class="result-card">' +
            '<div class="result-name">' + esc(b.name) + "</div>" +
            '<div class="result-meta">' +
            '<span>' + esc(b.category || "Uncategorized") + "</span>" +
            '<span>' + esc(b.area || "Unknown") + "</span>" +
            (b.distance_km ? '<span>' + b.distance_km + " km</span>" : "") +
            "</div>" +
            (badges ? '<div class="result-channels">' + badges + "</div>" : "") +
            scores +
            '<div class="result-cta">' + (b.primary_contact ? esc(b.primary_contact.label) : "View") + " &rarr;</div>" +
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
            render();
            window.scrollBy(0, 1);
        });
    }

    function render() {
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
        statsLine.textContent = Math.min(displayCount, total) + " of " + total + " results";
        renderLoadMore(total);
    }

    function resetAndRender() {
        displayCount = PAGE_SIZE;
        render();
    }

    searchInput.addEventListener("input", resetAndRender);
    catFilter.addEventListener("change", resetAndRender);
    areaFilter.addEventListener("change", resetAndRender);
    channelFilter.addEventListener("change", resetAndRender);
    sortFilter.addEventListener("change", resetAndRender);

    populateFilters();
    render();
})();
