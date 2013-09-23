template "#{node[:nginx][:dir]}/sites-enabled/joltem.conf" do
    source      "joltem.conf.erb"
    owner       'root'
    group       'root'
    mode        '0644'
    notifies :reload, resources(:service => "nginx")
end
