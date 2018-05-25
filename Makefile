.PHONY: all screenshots

all:
	@./make.py

clean:
	rm -rf css

release:
	bash release.sh

screenshots:
	@./make.py screenshots
