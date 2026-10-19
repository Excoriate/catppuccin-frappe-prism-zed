#!/bin/sh
# ANSI-only sample: terminal theme colors remain the source of each foreground.
printf '\033[0m\033[2J\033[H'
printf 'FRAPPÉ PRISM  /  RETRO TERMINAL\n\n'
printf 'Plain foreground   build complete · ready to ship\n'
printf '\033[1mBright foreground  all checks passed\033[0m\n'
printf '\033[2mDim foreground     background work stays readable\033[0m\n\n'
printf '              black    red      green    yellow   blue     magenta  cyan     white\n'
for mode in normal bright dim; do
    printf '%-12s  ' "$mode"
    for index in 0 1 2 3 4 5 6 7; do
        case "$mode" in
            normal) code=$((30 + index)); prefix='' ;;
            bright) code=$((90 + index)); prefix='' ;;
            dim) code=$((30 + index)); prefix='2;' ;;
        esac
        printf '\033[%s%smANSI %s\033[0m   ' "$prefix" "$code" "$index"
    done
    printf '\n'
done
printf '\n\033[40;97m ANSI 40 black background / bright white foreground \033[0m\n'
printf '\n\033[7m Reverse video: selected process / active task \033[0m\n'
printf '\nSelect this plain green line to inspect terminal selection.\n'
printf 'Palette uses ANSI colors; applications can override them with truecolor.\n'
