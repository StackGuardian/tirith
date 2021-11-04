#!/bin/bash


		git status -sb | awk -F '[,.\\[\\]]' '\
			NR == 1 {
				b = gensub(/.* /, "", 1, $1)
				r = NF; s = "0"

				if(r > 4) for(f = 5; f < NF; f++) {
					#i = ($f ~ /^ ?a/) ? "  " : "  "
					#i = ($f ~ /^ ?a/) ? "  " : "  "
					#i = ($f ~ /^ ?a/) ? " ↑ " : " ↓ "
					#i = ($f ~ /^ ?a/) ? "  " : "  "
					#i = ($f ~ /^ ?a/) ? "  " : "  "
					i = ($f ~ /^ ?a/) ? "  " : "  "
					s = s gensub(/ ?.* /, i, 1, $f)
					system("~/.orw/scripts/notify.sh " s)
				}
			}

			NR > 1 {
				if(/^\s*M/) m++
				else if(/^\s*D/) d++
				else if(/^A/) a++
				else if(/^\?/) u++
				if(!/^\?/ && index($0, $1) == 1) i++
			}

			END {
				gm = "'$1'"
				if(gm ~ "m" && m) c = c " m=\"  "m"\""
				#if(gm ~ "i" && i) c = c " i=\"  "i"\""
				if(gm ~ "i" && i) c = c " i=\"  "i"\""
				if(gm ~ "d" && d) c = c " d=\"  "d"\""
				if(gm ~ "a" && a) c = c " a=\"  "a"\""
				if(gm ~ "u" && u) c = c " u=\"  "u"\""

				if(b) print b, (r > 1) ? "╋" : "┣", (NR == 1), s, c }'

