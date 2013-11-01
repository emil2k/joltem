#
# Cookbook Name:: pypi
# Recipe:: default
#
# Copyright 2013, Kirill Klenov

PYPI_DIR = "#{node['pypi']['deploy_dir']}" 
PYPI_PACKAGES_DIR = "#{PYPI_DIR}/packages" 

# Setup directory
directory PYPI_DIR do
    owner 'www-data'
    group "www-data"
    mode "0755"
    action :create
    recursive true
end

directory PYPI_PACKAGES_DIR do
    owner 'www-data'
    group "www-data"
    mode "0755"
    action :create
    recursive true
end

# Install Flask-Pypi-Proxy
python_pip "flask-pypi-proxy" do
    action :install
end

# Setup application
template "#{PYPI_DIR}/pypi.py" do
    source "app.py"
    owner "www-data"
    group "www-data"
    mode "0644"
end

# Install uwsgi
python_pip "uwsgi"

# Run uwsgi service
include_recipe "runit"
runit_service "pypi" do
    options ({
        :home_path => PYPI_DIR,
        :pid_path => "/var/run/pypi.pid",
        :host => "127.0.0.1",
        :port => node[:pypi][:port],
        :worker_processes => 1,
        :app => "pypi:app",
        :uid => "www-data",
        :gid => "www-data"
    })
end

# Setup nginx
template "#{node[:nginx][:directories][:conf_dir]}/sites-available/pypi.conf" do
    source      "nginx.erb"
    owner       'root'
    group       'root'
    mode        '0644'

    notifies :reload, resources(:service => "nginx")
end
nginx_site "pypi"
