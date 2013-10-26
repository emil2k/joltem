template "#{node[:nginx][:directories][:conf_dir]}/sites-enabled/joltem.conf" do
    source      "nginx/joltem.conf.erb"
    owner       'root'
    group       'root'
    mode        '0644'
    notifies :reload, resources(:service => "nginx")
end
