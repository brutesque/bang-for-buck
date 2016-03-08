#!/bin/bash


# Exit this script on the first error.
#------------------------------------------------------------------------------
set -e


# Collect data.
#------------------------------------------------------------------------------

python get_octane_scores.py
python get_tweakers_prices.py
python db_to_html.py


# Update git repository and push to gh-pages.
#------------------------------------------------------------------------------

git checkout gh-pages
mv /tmp/octane_tweakers.html ./index.html
mv /tmp/octane_tweakers.db ./octane_tweakers.db
git commit -am "automated update"
git push
git checkout master


# Finished.
#------------------------------------------------------------------------------
echo 'Update successfull'
