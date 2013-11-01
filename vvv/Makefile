RED=\033[0;31m
NC=\033[0m
CLIENT=$(shell echo $${CLIENT:-$$USER})

ROLEDIR=roles
COOKBOOKDIR=cookbooks
DATABAGDIR=data_bags
ENVIRONMENTDIR=environments

all: user.rb help

.PHONY: help
# target: help          - Display callable targets
help:
	@egrep "^# target:" [Mm]akefile | sed -e 's/^# target: //g' | sort

.PHONY: status
# target: status        - Display node's status
status:
	@echo "$(RED)knife status$(NC)\n"
	@knife status

.PHONY: cookbooks
# target: cookbooks     - Upload cookbooks to chef server
cookbooks:
	@echo "$(RED)knife cookbook upload -a$(NC)\n"
	@knife cookbook upload -a

.PHONY: roles
# target: roles         - Upload roles to chef server
roles:
	@echo "$(RED)knife role from file $(ROLEDIR)/*.json$(NC)\n"
	@knife role from file $(ROLEDIR)/*.json

.PHONY: data_bags
# target: data_bags     - Upload data bags to chef server
data_bags:
	@for file in `find $(DATABAGDIR) -name '*.json'`; do \
	    data_bag=$$(basename $$(dirname $$file)); \
	    knife data bag create $$data_bag; \
	    knife data bag from file $$data_bag $$file; \
	done

.PHONY: environments
# target: environments  - Upload environments to chef server
environments:
	@echo "$(RED)knife environment from file $(ENVIRONMENTDIR)/environments/*.rb\n$(NC)"
	@knife environment from file $(ENVIRONMENTDIR)/*.rb

user.rb: $(CLIENT).pem
	@echo $(CLIENT)
	@echo '$$client_name = "$(USER)"' >> user.rb
	@echo '$$client_fullname = "$(DEBFULLNAME)"' >> user.rb
	@echo '$$client_email = "$(DEBEMAIL)"' >> user.rb
	@echo "$(RED)'user.rb' created.$(NC)"

$(CLIENT).pem:
	@echo "$(RED)Copy your private key to $(USER).pem$(NC)"
