(function () {
    var searchInput = document.getElementById("cl-search");
    var resultsDiv = document.getElementById("cl-results");
    var countDiv = document.getElementById("cl-count");
    var allSections = document.querySelectorAll(".cl-cat-heading, .cl-grid");

    function esc(s) {
        if (!s) return "";
        var d = document.createElement("div");
        d.textContent = s;
        return d.innerHTML;
    }

    function renderCard(ad) {
        var tags = (ad.tags || []).map(function (t) {
            return '<span class="channel-tag">' + esc(t) + "</span>";
        }).join("");
        return '<a href="../classifieds/' + ad.slug + '.html" class="cl-card">' +
            '<div class="cl-title">' + esc(ad.title) + "</div>" +
            '<div class="cl-meta">' + esc(ad.area || "") + " &middot; " + esc(ad.price || "Free") + "</div>" +
            '<div class="cl-summary">' + esc(ad.summary.slice(0, 120)) + "</div>" +
            (tags ? '<div class="cl-tags">' + tags + "</div>" : "") +
            '<div class="cl-date">' + ad.posted_date + "</div>" +
            "</a>";
    }

    function render() {
        var q = searchInput.value.toLowerCase().trim();
        if (!q) {
            // Show all categories
            var html = "";
            var cats = {};
            CLASSIFIEDS.forEach(function (ad) {
                cats[ad.category] = (cats[ad.category] || 0) + 1;
            });
            Object.keys(cats).sort().forEach(function (cat) {
                var label = (CL_LABELS[cat] || cat) + " (" + cats[cat] + ")";
                html += "<h2 class='cl-cat-heading'>" + label + "</h2><div class='cl-grid'>";
                CLASSIFIEDS.filter(function (ad) { return ad.category === cat; }).forEach(function (ad) {
                    html += renderCard(ad);
                });
                html += "</div>";
            });
            resultsDiv.innerHTML = html;
            countDiv.textContent = CLASSIFIEDS.length + " listings";
            return;
        }

        var matching = CLASSIFIEDS.filter(function (ad) {
            var inTitle = ad.title.toLowerCase().includes(q);
            var inSummary = (ad.summary || "").toLowerCase().includes(q);
            var inArea = (ad.area || "").toLowerCase().includes(q);
            var inTags = (ad.tags || []).some(function (t) { return t.toLowerCase().includes(q); });
            return inTitle || inSummary || inArea || inTags;
        });

        if (matching.length === 0) {
            resultsDiv.innerHTML = '<div class="no-results">No classifieds match "' + esc(q) + '". <a href="mailto:paradisio@example.com?subject=Post%20classified&body=Category:%0ATitle:%0APrice:%0AArea:%0AContact:%0ADescription:">Post the ad yourself</a>.</div>';
            countDiv.textContent = "0 results";
            return;
        }

        var html = matching.map(renderCard).join("");
        resultsDiv.innerHTML = '<div class="cl-grid">' + html + "</div>";
        countDiv.textContent = matching.length + " of " + CLASSIFIEDS.length + " listings";
    }

    searchInput.addEventListener("input", render);
    render();
})();
