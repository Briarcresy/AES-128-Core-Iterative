#!/usr/bin/env bash

set -eu

result_dir=$1
design=$2
clock_mhz=$3

area_report="$result_dir/synth_stat.txt"
timing_report="$result_dir/$design.rpt"
power_report="$result_dir/$design.pwr"

for report in "$area_report" "$timing_report" "$power_report"; do
    if [ ! -f "$report" ]; then
        printf 'Missing report: %s\n' "$report" >&2
        exit 1
    fi
done

if [ -t 1 ] && [ -z "${NO_COLOR:-}" ]; then
    green='\033[1;32m'
    red='\033[1;31m'
    yellow='\033[1;33m'
    cyan='\033[1;36m'
    reset='\033[0m'
else
    green=''
    red=''
    yellow=''
    cyan=''
    reset=''
fi

area=$(awk '/Chip area for module/ {print $NF; exit}' "$area_report")
cells=$(awk '$NF == "cells" {print $1; exit}' "$area_report")
power=$(awk '/^Total Power/ {print $(NF-1), $NF; exit}' "$power_report")
internal_power=$(awk '/^Cell Internal Power/ {print $(NF-1), "W"; exit}' "$power_report")
leakage_power=$(awk '/^Cell Leakage Power/ {print $(NF-1), "W"; exit}' "$power_report")

read -r setup_wns setup_freq hold_wns <<EOF
$(awk -F '|' '
function trim(s) {gsub(/^[ \t]+|[ \t]+$/, "", s); return s}
trim($3) == "test_clock" && trim($4) == "max" {
    slack = trim($8) + 0
    if (!have_setup || slack < setup) {
        setup = slack
        freq = trim($9)
        have_setup = 1
    }
}
trim($3) == "test_clock" && trim($4) == "min" {
    slack = trim($8) + 0
    if (!have_hold || slack < hold) {
        hold = slack
        have_hold = 1
    }
}
END {printf "%.3f %s %.3f\n", setup, freq, hold}
' "$timing_report")
EOF

read -r setup_tns hold_tns <<EOF
$(awk -F '|' '
function trim(s) {gsub(/^[ \t]+|[ \t]+$/, "", s); return s}
trim($2) == "test_clock" && trim($3) == "max" {setup = trim($4)}
trim($2) == "test_clock" && trim($3) == "min" {hold = trim($4)}
END {print setup, hold}
' "$timing_report")
EOF

status_color() {
    awk -v value="$1" 'BEGIN {exit !(value >= 0)}'
}

printf '\n%b%s PPA Summary%b\n' "$cyan" "$design" "$reset"
printf '%s\n' '----------------------------------------'
printf '%bPower%b\n' "$cyan" "$reset"
printf '  Total estimate : %s\n' "$power"
printf '  Internal       : %s\n' "$internal_power"
printf '  Leakage        : %s\n' "$leakage_power"
printf '  %bNote: no switching activity was supplied; treat power as preliminary.%b\n' "$yellow" "$reset"

printf '%bPerformance%b\n' "$cyan" "$reset"
printf '  Target clock   : %s MHz\n' "$clock_mhz"
printf '  Reported Fmax  : %s MHz\n' "$setup_freq"
if status_color "$setup_wns"; then
    printf '  Setup          : %bPASS%b  WNS=%s ns, TNS=%s ns\n' "$green" "$reset" "$setup_wns" "$setup_tns"
else
    printf '  Setup          : %bVIOLATED%b  WNS=%s ns, TNS=%s ns\n' "$red" "$reset" "$setup_wns" "$setup_tns"
fi
if status_color "$hold_wns"; then
    printf '  Hold           : %bPASS%b  WNS=%s ns, TNS=%s ns\n' "$green" "$reset" "$hold_wns" "$hold_tns"
else
    printf '  Hold           : %bVIOLATED%b  WNS=%s ns, TNS=%s ns\n' "$red" "$reset" "$hold_wns" "$hold_tns"
fi

printf '%bArea%b\n' "$cyan" "$reset"
printf '  Cell area      : %s um^2\n' "$area"
printf '  Cell count     : %s\n' "$cells"
printf '%s\n\n' '----------------------------------------'
