template "#{node[:joltem][:path]}/joltem/settings/chefenv.py" do
    source      "django/settings.py.erb"
    mode        '0644'
end

