#!/bin/sh
# extract-landmarks.sh - regenerate the LANDMARKS array for map-navigator.html
#
# Scans a crossfire-maps checkout for the region designation of every bigworld
# tile (world/world_<x>_<y>), picks one representative tile per named region
# (the region tile closest to the region's centroid), and prints a JavaScript
# array ready to paste into the LANDMARKS definition in map-navigator.html.
#
# Display names come from the longname entries in regions.reg; regions without
# a longname fall back to a capitalized region code.
#
# Usage:
#   tools/extract-landmarks.sh /path/to/crossfire-maps
#
# Example:
#   tools/extract-landmarks.sh ~/cf-devel/crossfire-crossfire-maps

set -eu

if [ $# -ne 1 ]; then
    echo "usage: $0 /path/to/crossfire-maps" >&2
    exit 2
fi

MAPS=$1
REG="$MAPS/regions.reg"

if [ ! -d "$MAPS/world" ]; then
    echo "error: $MAPS/world not found (not a crossfire-maps checkout?)" >&2
    exit 1
fi
if [ ! -f "$REG" ]; then
    echo "warning: $REG not found; falling back to region codes for names" >&2
    REG=/dev/null
fi

# shellcheck disable=SC2035
awk '
    # --- regions.reg: build code -> longname table -------------------------
    FILENAME ~ /regions\.reg$/ || FILENAME == "/dev/null" {
        if ($1 == "region") cur = $2
        if ($1 == "longname" && cur != "") {
            sub(/^longname[ \t]+/, "")
            long_name[cur] = $0
        }
        next
    }

    # --- world tiles: first region line names the tile ---------------------
    FNR == 1 { seen = 0 }
    seen == 0 && $1 == "region" {
        seen = 1
        r = $2
        if (r == "world" || r == "") next
        n = split(FILENAME, part, "/")
        if (split(part[n], c, "_") != 3) next   # expect world_<x>_<y>
        x = c[2] + 0; y = c[3] + 0
        cnt[r]++
        sumx[r] += x; sumy[r] += y
        tx[r, cnt[r]] = x; ty[r, cnt[r]] = y
    }

    # --- pick the tile closest to each region centroid ---------------------
    END {
        for (r in cnt) {
            cx = sumx[r] / cnt[r]; cy = sumy[r] / cnt[r]
            best = 1
            bestd = (tx[r,1]-cx)^2 + (ty[r,1]-cy)^2
            for (i = 2; i <= cnt[r]; i++) {
                d = (tx[r,i]-cx)^2 + (ty[r,i]-cy)^2
                # tie-break: northwest-most tile, for deterministic output
                if (d < bestd || (d == bestd && \
                    (tx[r,i] < tx[r,best] || \
                    (tx[r,i] == tx[r,best] && ty[r,i] < ty[r,best])))) {
                    best = i; bestd = d
                }
            }
            name = (r in long_name) ? long_name[r] : toupper(substr(r,1,1)) substr(r,2)
            printf "%s\t%d\t%d\t%d\n", name, tx[r,best], ty[r,best], cnt[r]
        }
    }
' "$REG" "$MAPS"/world/world_* |
sort -f |
awk -F '\t' '
    BEGIN {
        print "  // Landmarks extracted from the region designations in the map source files."
        print "  // Regenerate with: tools/extract-landmarks.sh /path/to/crossfire-maps"
        print "  var LANDMARKS = ["
    }
    {
        line[NR] = sprintf("    { name: %-24s x: %d, y: %d }", \
                           sprintf("'\''%s'\'',", $1), $2, $3)
        total += $4
    }
    END {
        for (i = 1; i <= NR; i++)
            print line[i] (i < NR ? "," : "")
        print "  ];"
        printf "extracted %d landmarks from %d region-tagged tiles\n", NR, total > "/dev/stderr"
    }
'
