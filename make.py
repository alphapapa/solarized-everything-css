#!/usr/bin/env python3

# * Imports

import os
import subprocess
import multiprocessing
import functools

from collections import namedtuple

# * Variables

sites_dir="sites"
themes_dir = "themes"
css_dir = "css"

common_deps = ["styl/index.styl", "styl/mixins.styl"]

CSS = namedtuple("CSS", ['path', 'deps', 'theme', 'site'])

# * Functions

def main():
    "Build CSS files that need to be built."

    css_files = list_css(themes(), sites())

    # Make directories first to avoid race condition
    for css in css_files:
        dir = os.path.join(css_dir, css.theme)
        if not os.path.isdir(dir):
            os.makedirs(dir)

    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    pool.map(build, css_files)

def build(css):
    "Build CSS file if necessary."

    css_mtime = mtime(css.path)
    make = False

    for dep in css.deps:
        if mtime(dep) > css_mtime:
            make = True
            break

    if make:
        stylus(css)

def stylus(css):
    "Run Stylus to build CSS file."

    output_file = css.path

    command = ["stylus", "--include", "styl",
               "--import", "themes/%s.styl" % css.theme,
               "--import", "styl",
               "-p", "sites/%s.styl" % css.site]
    result = subprocess.check_output(command)

    with open(output_file, "wb") as f:
        f.write(result)
        print(output_file)

def list_css(themes, sites):
    "Return list of CSS files for THEMES and SITES."

    return [CSS("%s/%s/%s.css" % (css_dir, theme, site),
                dependencies(theme, site), theme, site)
            for theme in themes
            for site in sites]

def themes():
    "Return list of themes."

    for path, dirs, files in os.walk(themes_dir):
        return [theme.replace(".styl", "") for theme in files]

def sites():
    "Return list of sites."

    for path, dirs, files in os.walk(sites_dir):
        return [site.replace(".styl", "") for site in files]

def dependencies(theme, site):
    "Return list of dependency .styl files for THEME and SITE."

    deps = list(common_deps)
    deps += ["themes/%s.styl" % theme, "sites/%s.styl" % site]

    if site == "all-sites":
        deps += ["sites/%s.styl" % s for s in sites()]

    return deps

@functools.lru_cache()
def mtime(path):
    "Return mtime for PATH."

    if os.path.isfile(path):
        return os.path.getmtime(path)
    else:
        return 0

# * Footer

if __name__ == "__main__":
    main()
