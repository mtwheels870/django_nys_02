#!/bin/bash
# -*- coding: utf-8 -*-
#
# DISTRIBUTION STATEMENT A. Approved for public release. Distribution is unlimited.
#
# This material is based upon work supported by the United States Air Force under Air Force Contract No. FA8702-15-D-0001. Any opinions, findings, conclusions or recommendations expressed
 in this material are those of the author(s) and do not necessarily reflect the views of the United States Air Force.
#
# © 2020 Massachusetts Institute of Technology.
#
# The software/firmware is provided to you on an As-Is basis
#
# Delivered to the U.S. Government with Unlimited Rights, as defined in DFARS Part 252.227-7013 or 7014 (Feb 2014). Notwithstanding any copyright notice, U.S. Government rights in this wo
rk are defined by DFARS 252.227-7013 or DFARS 252.227-7014 as detailed above. Use of this work other than as specifically authorized by the U.S. Government may violate any copyrights that
 exist in this work.

# Scan Options
ports=(icmp)
scanRate=5000
baseDir="/opt/cyber/feb27storm"
whitelistFile="networks-feb27storm_20250117.csv"
DEBUG=True
blacklistFile="/home/ubuntu/venv/python/cyberpow/resources/zmap/blacklist.txt"

# These shouldn't change
outputDir="${baseDir}/PORT_results"
now=$(date -u +"%Y-%m-%dT%H%M")
resultsFile="${outputDir}/results_PORT_${now}.csv"
consoleFile="${outputDir}/console_PORT_${now}.csv"
metadataFile="${outputDir}/metadata_PORT_${now}.csv"
logFile="${outputDir}/log_PORT_${now}"

# Zmap Config
zmapCmdArgs="--rate=${scanRate} --whitelist-file=${baseDir}/${whitelistFile} --blacklist-file=${blacklistFile} --output-file=${resultsFile} --output-module=csv  --output-fields=saddr,time
stamp-ts --metadata-file=${metadataFile} --sender-threads=1 --log-file=${logFile}"
zmapTcpArgs="--probe-module=tcp_synscan --target-port=PORT"
zmapIcmpArgs="--probe-module=icmp_echoscan"

# Perform Scans
for port in "${ports[@]}"
do
    # make the output directory for this port
    #  substitute the actual port number in place of the PORT placeholder
    dirToMake=${outputDir//PORT/$port}
    eval "mkdir -p $dirToMake"
    #echo "mkdir $dirToMake"

    # construct the resources.zmap command with the appropriate set of arguments
    zmapCmd="zmap"
    if [ "$port" == "icmp" ]
    then
        zmapCmd="$zmapCmd $zmapIcmpArgs $zmapCmdArgs > ${consoleFile} 2>&1"
    else
        zmapCmd="$zmapCmd $zmapTcpArgs $zmapCmdArgs > ${consoleFile} 2>&1"
    fi

    #  substitute the actual port number in place of the PORT placeholder
    zmapCmd=${zmapCmd//PORT/$port}

    # execute the command
    eval "sudo $zmapCmd"
    #echo "$zmapCmd"
done
