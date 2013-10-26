cache_dir       = Chef::Config[:file_cache_path]

package "cmake"

execute "Clone libgit2" do
  cwd       cache_dir
  command   <<-COMMAND
    rm -rf libgit2
    git clone git://github.com/libgit2/libgit2.git -b master
  COMMAND

  creates   "#{cache_dir}/libgit2"
end

execute "Build libgit2" do
  cwd       "#{cache_dir}/libgit2"
  command   <<-COMMAND
    cmake .
    cmake --build . --target install
  COMMAND

  creates   "/usr/local/lib/libgit2.so.0.19.0"
end

