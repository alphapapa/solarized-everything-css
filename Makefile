# ** Variables
VPATH = .:sites
CSS_DIR := css
COLORS := light dark

COMMON_FILES := $(wildcard *.styl)
SITES := $(patsubst sites/%.styl,%,$(wildcard sites/*.styl))

# ** Functions
make_site = for color in $(COLORS); do stylus --import $$color.styl -p sites/$(1).styl >$(CSS_DIR)/solarized-$(1)-$$color.css; done

# ** Rules
.PHONY: all
all: $(SITES)

$(CSS_DIR):
	mkdir $(CSS_DIR)

$(SITES): %: $(CSS_DIR)/solarized-%-dark.css $(CSS_DIR)/solarized-%-light.css

$(foreach color, $(COLORS), $(CSS_DIR)/solarized-%-$(color).css): sites/%.styl $(COMMON_FILES) | $(CSS_DIR)
	$(call make_site,$*)
