(function () {
    var currentLang = localStorage.getItem("paradisio_lang") || "en";
    var supportedLangs = Object.keys(LOCALE_DATA || {});

    function t(key, vars) {
        var lang = LOCALE_DATA[currentLang] || LOCALE_DATA["en"] || {};
        var val = lang[key] || LOCALE_DATA["en"] ? (LOCALE_DATA["en"][key] || key) : key;
        if (vars) {
            for (var k in vars) {
                val = val.replace("{" + k + "}", vars[k]);
            }
        }
        return val;
    }

    function translatePage() {
        document.querySelectorAll("[data-i18n]").forEach(function (el) {
            var key = el.getAttribute("data-i18n");
            var translated = t(key);
            if (translated && translated !== key) {
                el.textContent = translated;
            }
        });
        document.querySelectorAll("[data-i18n-placeholder]").forEach(function (el) {
            var key = el.getAttribute("data-i18n-placeholder");
            var translated = t(key);
            if (translated && translated !== key) {
                el.placeholder = translated;
            }
        });
        // Update active lang button
        document.querySelectorAll(".lang-btn").forEach(function (btn) {
            btn.classList.toggle("lang-active", btn.getAttribute("data-lang") === currentLang);
        });
        document.documentElement.lang = currentLang;
    }

    function setLang(lang) {
        if (!supportedLangs.includes(lang)) return;
        currentLang = lang;
        localStorage.setItem("paradisio_lang", lang);
        translatePage();
        // Dispatch event for dynamic components
        document.dispatchEvent(new CustomEvent("langchange", { detail: { lang: lang } }));
    }

    // Language switcher clicks
    document.addEventListener("click", function (e) {
        var btn = e.target.closest(".lang-btn");
        if (btn) {
            e.preventDefault();
            setLang(btn.getAttribute("data-lang"));
        }
    });

    // Expose for app.js use
    window.__ = t;
    window.setLang = setLang;
    window.getLang = function () { return currentLang; };

    // Run on load
    document.addEventListener("DOMContentLoaded", translatePage);
    // Also run immediately if DOM already loaded
    if (document.readyState === "complete" || document.readyState === "interactive") {
        translatePage();
    }
})();
