#
# Cookbook Name:: nginx
# Attributes:: default
#
# Author:: Adam Jacob (<adam@opscode.com>)
# Author:: Joshua Timberman (<joshua@opscode.com>)
#
# Copyright 2009-2011, Opscode, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

default[:nginx][:version]                       = "1.0.11"

default[:nginx][:directories][:conf_dir]        = "/etc/nginx"
default[:nginx][:directories][:log_dir]         = "/var/log/nginx"
default[:nginx][:user]                          = "www-data"
default[:nginx][:directories][:binary]          = "/usr/sbin/nginx"

default[:nginx][:gzip][:enable] = "on"
default[:nginx][:gzip][:gzip_http_version] = "1.0"
default[:nginx][:gzip][:gzip_comp_level] = "4"
default[:nginx][:gzip][:gzip_proxied] = "any"
default[:nginx][:gzip][:gzip_disable] = "msie6"
default[:nginx][:gzip][:gzip_vary] = "off"
default[:nginx][:gzip][:gzip_types] = [
  "text/plain",
  "text/css",
  "application/x-javascript",
  "text/xml",
  "application/xml",
  "application/xml+rss",
  "text/javascript",
  "application/json"
]

default[:nginx][:keepalive]                     = "on"
default[:nginx][:keepalive_timeout]             = 65
default[:nginx][:worker_processes]              = cpu[:total]
default[:nginx][:worker_connections]            = 8192
default[:nginx][:server_names_hash_bucket_size] = 64
default[:nginx][:worker_rlimit_nofile]          = 8192
default[:nginx][:types_hash_bucket_size]        = 64
default[:nginx][:client_max_body_size]          = 128
