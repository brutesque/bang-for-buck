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

###


# Finished.
#------------------------------------------------------------------------------
echo 'Update successfull'
