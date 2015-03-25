# varnishtuner.py
Varnish Cache Tuner

This python script checks Varnish stats and server settings hoping to recommend optimal values for Varnish Cache parameters. Script is currently an alpha release and is plagued with bugs and issues. It's also written to work with a subset of Varnish deployments (namely those we target with our cPanel Varnish and cPanel Varnish Nginx plugins - see http://www.unixy.net/varnish/ ). Patches are welcome!

What's the precursor for writing this script?

First, there's the need to remove the complexity from correctly adjusting Varnish parameters. Second, there was no freely available script that does it (Varnish Software's own varnish tuner script is doubly not free).

Why is the script reinventing the wheel instead of leveraging Python external modules?

We're aiming to support 2.4,2.6,and 3.x Python installations. The goal is to have code that semi-works with all of these fragmented releases. So the script does not rely on installing modules. It's one file that runs on as many environments as possible.

How do I run it?

1. wget https://raw.githubusercontent.com/unixy/varnishtuner.py/master/varnishtuner.py

2. python varnishtuner.py
