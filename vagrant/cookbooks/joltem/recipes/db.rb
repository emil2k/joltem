pg_user node[:joltem][:db][:user] do
    privileges :superuser => false, :createdb => false, :login => true
    password node[:joltem][:db][:password]
end

pg_database node[:joltem][:db][:name] do
    owner node[:joltem][:db][:user]
    encoding "utf8"
    template "template0"
    locale "en_US.UTF8"
end
