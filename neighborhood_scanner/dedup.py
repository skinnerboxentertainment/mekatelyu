"""
Deduplication engine for the neighborhood scanner.
Loads known businesses, normalizes names, provides fuzzy matching.
"""
import csv
import re

KNOWN_FILES = [
    "pv_within_5km_enriched_b.csv",
    "pv_within_5km_verified_additions_enriched.csv",
]


def normalize(name):
    if not name:
        return ""
    n = name.lower().strip()
    n = re.sub(r"[^\w\s]", "", n)
    n = re.sub(r"\s+", " ", n)
    # Remove common location suffixes
    n = re.sub(r"\s*[-–—]\s*(puerto viejo|cocles|playa negra|playa chiquita|punta uva|manzanillo|hone creek|cahuita|limon|limón|costa rica).*$", "", n)
    return n.strip()


def name_tokens(name):
    return set(normalize(name).split())


class DedupEngine:
    def __init__(self):
        self.known_names = []
        self.known_norm = {}
        self.known_tokens = {}

    def load(self, files=None):
        if files is None:
            files = KNOWN_FILES
        for f in files:
            try:
                with open(f, encoding="utf-8-sig", newline="") as fh:
                    for row in csv.DictReader(fh):
                        name = (row.get("business_name") or "").strip()
                        if name and normalize(name):
                            if name not in self.known_norm:
                                self.known_names.append(name)
                                self.known_norm[name] = normalize(name)
                                self.known_tokens[name] = name_tokens(name)
            except FileNotFoundError:
                pass
        print(f"DedupEngine: loaded {len(self.known_names)} known businesses")

    def is_known(self, name, threshold=0.6):
        """Check if a name is likely already in our dataset."""
        n = normalize(name)
        if not n:
            return True
        t = set(n.split())

        for kn in self.known_names:
            kn_n = self.known_norm[kn]

            # Exact match
            if n == kn_n:
                return kn

            # Substring match
            if len(n) > 4 and (n in kn_n or kn_n in n):
                return kn

            # Token overlap
            knt = self.known_tokens[kn]
            if not t or not knt:
                continue
            overlap = len(t & knt)
            smaller = min(len(t), len(knt))
            if smaller <= 2:
                if overlap >= smaller:
                    return kn
            elif overlap / smaller >= threshold:
                return kn

        return None

    def bulk_check(self, names, threshold=0.6):
        """Check many names at once. Returns dict of name -> known_name or None."""
        return {n: self.is_known(n, threshold) for n in names}

    def get_known_names(self):
        return self.known_names
