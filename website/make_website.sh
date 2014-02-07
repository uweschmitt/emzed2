#!/bin/sh
sphinx-build -b html -d _build/doctrees . _build/html
cp _themes/emzed/pygments_patched.css _build/html/_static/pygments.css
