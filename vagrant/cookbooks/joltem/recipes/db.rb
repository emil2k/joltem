include_recipe "mysql::ruby"

mysql_connection_info = {
    :host => node[:joltem][:db][:host],
    :username => 'root',
    :password => node[:mysql][:server_root_password]
}

mysql_database node[:joltem][:db][:name] do
    connection mysql_connection_info
    action :create
end

mysql_database_user node[:joltem][:db][:user] do
    connection mysql_connection_info
    password node[:joltem][:db][:password]
    action :create
end

mysql_database_user node[:joltem][:db][:user] do
    connection mysql_connection_info
    password node[:joltem][:db][:password]
    database_name node[:joltem][:db][:name]
    action :grant
end
