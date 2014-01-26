autowikibot
===========

Reddit bot that replies to comments with excerpt from linked wikipedia article or section.

Current instance:

[See bot in action](http://www.reddit.com/u/autowikibot) |
[Subreddit](http://www.reddit.com/r/autowikibot/)

Features
========

* Responds to comments like "wikibot, what is dancing?" and  "wikibot, tell me about enigma machine"
* In-post summoning to keywords. e.g. I guess, OP should add some more ?- Liverwurst -? to the recipe
* Suggest upto 4 related interesting articles
* Deletes on parent commenter command
* Deletes if comment score below threshold
* User blacklist
* Automated subreddit blacklisting on first HTTP 403 encountered

Requirements
============

Tested in Python 2.7.6
* `pip install praw`
* `pip install pyimgur`
* `pip install beautifulsoup4`
* `pip install wikipedia`
* `apt-get install memcached`
* `apt-get install python-memcache`

These ones were used in kiwix-version, which is now deprecated
* `pip install BeautifulSoup`
* `easy_install twitter`


License
=========

This bot is licensed under [**Creative Commons Attribution-ShareAlike 3.0 Unported license**](http://creativecommons.org/licenses/by-sa/3.0/)

Attribution: Include URL to this github page in your README (or similar) file, or at start of code.
