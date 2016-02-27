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

### git push origin `git subtree split --prefix site master 2> /dev/null`:gh-pages --force


# Finished.
#------------------------------------------------------------------------------
echo 'Update successfull'
