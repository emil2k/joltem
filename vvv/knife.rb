load './user.rb'

current_dir = File.dirname(__FILE__)

log_level               :info
log_location            STDOUT
node_name               $client_name
client_key              "#{current_dir}/#{$client_name}.pem"
validation_client_name  "chef-validator"
validation_key          "#{current_dir}/validator.pem"

chef_server_url         "https://chef.joltem.com"
cache_type              "BasicFile"
cache_options( :path => "#{ENV['HOME']}/.chef/checksums" )

cookbook_path           ["#{current_dir}/cookbooks"]
cookbook_copyright      $client_fullname
cookbook_email          $client_email
cookbook_license        "MIT"

data_bag_path           "#{current_dir}/data_bags"
role_path               "#{current_dir}/roles"

