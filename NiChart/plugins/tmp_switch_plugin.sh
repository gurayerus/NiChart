#! /bin/bash +x

p=$1

if [ -z $p ]; then
	echo "Usage: $0 pluginname"
	exit 1
fi

if [ -e ${p}/${p}.yapsy-plugin ]; then
	mv ${p}/${p}.yapsy-plugin ${p}/${p}.yapsy-plugin_disabled -v
else
	if [ -e ${p}/${p}.yapsy-plugin_disabled ]; then
        	mv ${p}/${p}.yapsy-plugin_disabled ${p}/${p}.yapsy-plugin -v
	fi
fi

