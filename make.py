#!/usr/bin/env python3

# * Imports

import os
import shutil
import subprocess
import sys
import multiprocessing
import functools

from collections import namedtuple
from tempfile import mkstemp

# * Variables

sites_dir="sites"
themes_dir = "themes"
css_dir = "css"
screenshots_dir="screenshots"

phantomjs_command = "phantomjs --ssl-protocol=any --ignore-ssl-errors=true screenshot.js".split()

common_deps = ["styl/index.styl", "styl/mixins.styl"]

CSS = namedtuple("CSS", ['path', 'deps', 'theme', 'site'])
Theme = namedtuple("Theme", ['name', 'styl_path', 'support_files'])

# * Functions

def main():
    "Update CSS files by default, or update screenshots."

    if len(sys.argv) > 1 and sys.argv[1] == "screenshots":
        update_screenshots()
    else:
        update_css_files()

# ** CSS

def update_css_files():
    "Build CSS files that need to be built."

    css_files = list_css(themes(), sites())

    # Make directories first to avoid race condition
    for css in css_files:
        dir = os.path.join(css_dir, css.theme.name)
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
               "--import", css.theme.styl_path,
               "--import", "styl",
               "-p", "sites/%s.styl" % css.site]
    result = subprocess.check_output(command)

    with open(output_file, "wb") as f:
        f.write(result)
        print(output_file)

# ** Screenshots

def update_screenshots():
    "Update screenshots."

    css_files = list_css(themes(), sites())

    if not os.path.isdir(screenshots_dir):
        # If the directory does not exist, create a new worktree for it.
        # Assumes the screenshots branch exists.
        subprocess.call(["git", "worktree", "prune"])
        subprocess.call(["git", "worktree", "add",
                         screenshots_dir, "screenshots"])

    # Make directories first to avoid race condition
    for css in css_files:
        output_dir = os.path.join(screenshots_dir, css.theme.name)
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    pool.map(update_screenshot, css_files)
    commit_screenshots()

def commit_screenshots():
    if os.path.exists(os.path.join(screenshots_dir, ".git")):
        subprocess.call(["git", "-C", screenshots_dir,
                         "add", "-A"])
        # amend changes instead of keeping them to save space
        subprocess.call(["git", "-C", screenshots_dir,
                         "commit", "--amend", "-m", "Update screenshots"])
    else:
        print("screenshot dir was not a worktree, aborting commit")

def update_screenshot(css):
    "Update screenshot for CSS if necessary."

    screenshot_path = screenshot_path_for_css(css)
    if mtime(css.path) > mtime(screenshot_path):
        save_screenshot(css)

def screenshot_path_for_css(css):
    "Return path of screenshot for CSS."

    return os.path.join(screenshots_dir, css.theme.name, "%s.png" % css.site)

def save_screenshot(css):
    "Save screenshot for CSS."

    # Prepare filename
    screenshot_path = screenshot_path_for_css(css)

    # Get URL
    url = css_screenshot_url(css)
    if not url:
        # Screenshot disabled
        return False

    # Prepare command
    command = list(phantomjs_command)
    command.extend([url, screenshot_path, css.path])

    # Run PhantomJS
    subprocess.check_output(command)

    # Compress with pngcrush
    _, tempfile_path = mkstemp(suffix=".png")
    subprocess.check_output(["pngcrush", screenshot_path, tempfile_path], stderr=subprocess.DEVNULL)
    shutil.move(tempfile_path, screenshot_path)

    print(screenshot_path)

def css_screenshot_url(css):
    "Return URL for taking screenshots of CSS."

    # Get site URL
    site_url_filename = os.path.join(sites_dir, css.site + ".url")
    if os.path.exists(site_url_filename):
        with open(site_url_filename, "r") as f:
            url = f.readlines()
            if url:
                # Use URL given in .url file
                url = url[0].strip()
    else:
        # Use name of site file (without .styl extension)
        url = "http://" + css.site

    return url

# ** Support

def list_css(themes, sites):
    "Return list of CSS files for THEMES and SITES."

    return [CSS("%s/%s/%s-%s.css" % (css_dir, theme.name, theme.name,
                                     site.strip('_')),
                dependencies(theme, site), theme, site)
            for theme in themes
            for site in sites]

def themes():
    "Return list of themes."

    theme_names = []
    themes = []

    # Make list of theme directories
    for d in os.listdir(themes_dir):
        theme_names.append(d)

    # Iterate over theme directories
    for theme in theme_names:
        support_files = []
        variant_files = []
        directory = os.path.join(themes_dir, theme)

        # Iterate over files in theme directory
        for f in os.listdir(directory):
            path = os.path.join(themes_dir, theme, f)

            if f == "colors.styl":
                # Support file
                support_files.append(path)

            elif f.endswith(".styl"):
                # Theme file
                variant_files.append({'variant': without_styl(f), 'path': path})
            # Otherwise, not a relevant file

        # Add theme object to list
        if len(variant_files) == 1:
            # Only one variant: omit variant name from theme name
            themes.append(Theme(theme, variant_files[0]['path'], support_files))
        else:
            # Multiple variants: include variant name in theme name
            for f in variant_files:
                themes.append(Theme("%s-%s" % (theme, f['variant']), f['path'], support_files))

    return themes

def sites():
    "Return list of sites."

    for path, dirs, files in os.walk(sites_dir):
        return [site.replace(".styl", "")
                for site in files
                if site.endswith(".styl")]

def dependencies(theme, site):
    "Return list of dependency .styl files for THEME and SITE."

    deps = list(common_deps)
    deps.append(theme.styl_path)
    deps.extend(theme.support_files)
    deps.append("sites/%s.styl" % site)

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

def without_styl(s):
    """Return string S without ".styl" extension."""

    return s.replace(".styl", "")

# * Footer

if __name__ == "__main__":
    main()
