Autowikibot
===========

Reddit bot that replies to comments with excerpt from linked wikipedia article or section.

Current instance:
[In action](http://www.reddit.com/u/autowikibot) |
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


Configuration
=============

First, with your bot account, create 3 comments where they will not be removed by someone.

1. comment with banned users list separated by single newline
2. comment with excluded subreddits (without /r/) list separated by single newline
3. comment with a number indicating total number of posts made by bot. Set 0 at first setup.

Second, You need to create a file called datafile.inf and have following data in it on separate lines:

* reddit bot username
* reddit bot account password
* imgur client id
* ID of comment with banned users list
* ID of comment with excluded subreddits
* ID of comment with a number of total number of posts

The file will look something like this:

````
wikipedia_robot
botspassword
rt23rnsr2453fop
cetagti
cefsfs4
ce5gd56
````

License
=========

This bot is licensed under [**Creative Commons Attribution-ShareAlike 3.0 Unported license**](http://creativecommons.org/licenses/by-sa/3.0/)

Attribution: Include URL to this github page in your README (or similar) file, or at start of code.
