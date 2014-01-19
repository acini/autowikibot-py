autowikibot
===========

Bot that comments on reddit comments with excerpt from linked wikipedia article.

[See bot in action](http://www.reddit.com/u/autowikibot) |
[Subreddit](http://www.reddit.com/r/autowikibot/) |
[Bot Status](https://twitter.com/autowikibot) |
[Screenshots](https://github.com/nexarx/autowikibot-py/wiki/Screenshots)

Features
========

* Responds to comments like "wikibot, what is dancing?" and  "wikibot, tell me about enigma machine"
* Commenting on comments having single wikipedia link
* Deletion on request by parent commenter
* Deletion on comment score below threshold

Requirements
============

Tested in Python 2.7.3
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

This bot is licensed under **Creative Commons Attribution-ShareAlike 3.0 Unported license**.

http://creativecommons.org/licenses/by-sa/3.0/

