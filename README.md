# Testing & Build status

| Build  	| Status 	|
|----	|----	|
|Main image |	[![Docker Cloud Build Status](https://img.shields.io/docker/cloud/build/amrox/greencandle)](https://hub.docker.com/repository/docker/amrox/greencandle)	|
|Mysql image |	[![Docker Cloud Build Status](https://img.shields.io/docker/cloud/build/amrox/gc-mysql)](https://hub.docker.com/repository/docker/amrox/gc-mysql)	|
|Redis image |	[![Docker Cloud Build Status](https://img.shields.io/docker/cloud/build/amrox/gc-redis)](https://hub.docker.com/repository/docker/amrox/gc-redis)	|
|Webserver image |	[![Docker Cloud Build Status](https://img.shields.io/docker/cloud/build/amrox/webserver)](https://hub.docker.com/repository/docker/amrox/webserver)	|
|Dashboard image |	[![Docker Cloud Build Status](https://img.shields.io/docker/cloud/build/amrox/dashboard)](https://hub.docker.com/repository/docker/amrox/dashboard)	|
|Testing| [![Build Status](https://travis-ci.org/adiabuk/greencandle.svg?branch=master)](https://travis-ci.org/adiabuk/greencandle)|

# Releases
## 0.33
* More explicit debug logging
* Add buy/sell rules and strategy names to API dashboard
* Fix bugs with initial prod run
* Uncouple test trade and test run
* Do an initial prod run immediately after collecting initial data
* Fix and sort naming convention for environments, hosts, tiers, and containers
* Add scatter graphs for calculating drawdown
* Sync pricing with exchange when initiating and closing a trade
* fix intervals between trades
* Better deploy script
* Cleanup c9e environments
* Add divisor var to decide how much to buy whilst supporting varying number of pairs
* Fix for margin balance to exclude debt
* Get monthly aggregated percentage test results per pair
* Avoid missing data in API by only updating when all data has been collected
* Add stop loss support for test data (which doesn't contain intermittent prices)

## 0.32
* Clean up c9e envs
* Add 5MA to stag
* New k8s job script and update template
* Add initial support for margin trading
* Fetch balance from margin wallet
* Update gechodriver for graphing
* Fix buy/sell from API
* Display buy/sell status in API dashboard
* Better logging for graphs and minor tweaks
* Ensure HOSTNAME var is added to docker compose

## 0.31
* Improve efficiency for Redis data
* Fix bug with non-aligned epoch times
* Fix missing data in graphs
* Add mysql dump to test runs
* Improved testing template

## 0.30
* Create Kubernetes Template for running test runs at scale
* Make docker containers k8s-friendly
* Script for collecting all associated data for test run
* New test configstore env for kubernetes

## 0.29
* Upgrade all bootstraps to use Python 3.7.0
* Upgrade requirements to match dependencies
* Add local test framework and enforce running with git hooks
* Use separate bootstrap scripts for dev/prod/docker
* Test cleanup

## 0.28
* Add local testing framework
* Reduce number of connections to DB and Redis
* Add Volume indicator to graphs
* Add profit factor to test runs
* Allow custom number of klines for test data
* Synchronize test and prod config

## 0.27
* Create graphs for all pairs in config
* Create thumbnails for API
* Add closed trades to API
* Expose matched buy/sell rules to API
* Better cron timings
* Download historic prices and indicators and populate redis/graph

## 0.26
* Testing of docker instance functionality
* Combine API and GC into single image
* Log directly to journald with preserved severity
* More cleanup of wasted diskspace on host and containers
* Fix of engine using incomplete data to populate redis in live mode
* Release script to pull latest version tag and deploy
* Add AWS S3 fuse package to non-test server for backups and other data

## 0.25
* Add api for displaying current open trades with ability to sell
* Add local install to travis tests
* Fix Crontabs with dates in path
* Fix webserver reverse proxy paths
* General cleanup

## 0.24
* Fix paths for nginx reverse proxy
* Allow scipts to determine open trades
* Limit trades by time since previous trade
* Fix relaive path for image building


