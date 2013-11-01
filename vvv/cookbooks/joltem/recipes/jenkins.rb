host_name = node['jenkins']['http_proxy']['host_name'] || node['fqdn']

template "#{node[:nginx][:directories][:conf_dir]}/sites-available/jenkins.conf" do
  source      'nginx_jenkins.conf.erb'
  owner       'root'
  group       'root'
  mode        '0644'
  variables(
    :host_name        => host_name,
    :host_aliases     => node['jenkins']['http_proxy']['host_aliases'],
    :listen_ports     => node['jenkins']['http_proxy']['listen_ports'],
    :max_upload_size  => node['jenkins']['http_proxy']['client_max_body_size']
  )

  if File.exists?("#{node['nginx']['dir']}/sites-enabled/jenkins.conf")
    notifies  :restart, 'service[nginx]'
  end
end

nginx_site 'jenkins'
