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
3. comment with list of subreddits where bot will only reply to top level (root) comments
4. comment with a number indicating total number of posts made by bot. Set 0 at first setup.

Second, You need to create a file called datafile.inf and have following data in it on separate lines:

* reddit bot username
* reddit bot account password
* imgur client id
* ID of comment with banned users list
* ID of comment with excluded subreddits
* ID of comment with root only subreddits
* ID of comment with a number of total number of posts

The file will look something like this:

````
wikipedia_robot
botspassword
rt23rnsr2453fop
cetagti
cefsfs4
cef43fs
ce5gd56
````

License
=========

This source code is available under a modified version of GNU GPLv3. See the accompanying file LICENCE. 

There is an extra clause to prevent abusive scenarios like [these](http://www.reddit.com/r/autowikibot/comments/1w9t4e/impostor_bot_uallinonebot_spamming_with_double/cezzfhc). It reads:

````
  18. Use of Source Code 

  A "Creator Instance" is a Reddit user account which is operated and
maintained by original author of this source code and is used by the
Program for processing and replying to comments. A subreddit where a Creator
Instance has ability to submit comments to is referred to as "Covered Subreddit".
The source code (modified or unmodified) cannot be used for submitting comments
in Covered Subreddits when such comments serve the same purpose. The souce code
(modified or unmodified) cannot be used for purpose of harassing operator/s of
Creator Instance. This clause will override any other clauses in this licence
if it conflicts with them.
````
