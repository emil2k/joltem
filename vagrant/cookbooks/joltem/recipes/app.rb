package "git"
package "vim"
package "postgresql-server-dev-all"

apt_repository "libgit2" do
  uri "http://ppa.launchpad.net/xav0989/libgit2/ubuntu"
  distribution node['lsb']['codename']
  components ["main"]
  keyserver "keyserver.ubuntu.com"
  key "797674B4"
end

package "libgit2-0"
package "libgit2-dev"
