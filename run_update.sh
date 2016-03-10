#!/bin/bash


# Exit this script on the first error.
#------------------------------------------------------------------------------
set -e


# Get latest repository.
#------------------------------------------------------------------------------
git pull

# Collect data.
#------------------------------------------------------------------------------

python get_octane_scores.py
python get_tweakers_prices.py
python db_to_html.py


# Update git repository and push to gh-pages.
#------------------------------------------------------------------------------

mv octane_tweakers.html /tmp/
mv octane_tweakers.db /tmp/
git checkout gh-pages
mv /tmp/octane_tweakers.html ./index.html
mv /tmp/octane_tweakers.db ./
git commit -am "automated update"
git push
git checkout master


# Finished.
#------------------------------------------------------------------------------
echo 'Update successfull'
