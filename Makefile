# ** Variables
VPATH = .:sites
CSS_DIR := css
COLORS := light dark

COMMON_FILES := $(wildcard styl/*.styl)
SITES := $(patsubst sites/%.styl,%,$(wildcard sites/*))

# ** Functions
make_site = for color in $(COLORS); do stylus --include styl --import styl/$$color.styl --import styl -p sites/$(1).styl >$(CSS_DIR)/solarized-$(1)-$$color.css; done

# ** Rules
.PHONY: all
all: $(SITES)

$(CSS_DIR):
	mkdir $(CSS_DIR)

# Make all-sites explicitly depend on everything so it will be rebuilt when anything changes
$(CSS_DIR)/solarized-all-sites-*.css: $(wildcard sites/*)

$(SITES): %: $(CSS_DIR)/solarized-%-dark.css $(CSS_DIR)/solarized-%-light.css

$(foreach color, $(COLORS), $(CSS_DIR)/solarized-%-$(color).css): sites/%.styl $(COMMON_FILES) | $(CSS_DIR)
	$(call make_site,$*)
