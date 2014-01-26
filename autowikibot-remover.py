# -*- coding: utf-8 -*-
import praw, time, re, pickle, traceback, os
from util import success, warn, log, fail

### Uncomment to debug
#import logging
#logging.basicConfig(level=logging.DEBUG)

### Set root directory to script directory
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

r = praw.Reddit("autowikibot by /u/acini at /r/autowikibot")
deletekeyword = "delete"
excludekeyword = "leave me alone"
includekeyword = "follow me again"
global banned_users

### Login
with open ('datafile.inf', 'r') as myfile:
    datafile_lines=myfile.readlines()
USERNAME = datafile_lines[0].strip()
PASSWORD = datafile_lines[1].strip()
banned_users_comment = "t1_"+datafile_lines[3].strip()

Trying = True
while Trying:
        try:
                r.login(USERNAME, PASSWORD)
                success("LOGGED IN")
                Trying = False
        except praw.errors.InvalidUserPass:
                fail("WRONG USERNAME OR PASSWORD")
                exit()
        except Exception as e:
	  fail(e)
	  time.sleep(5)

def file_warning():
  fail("One or more of data files is not found or is corrupted.")
  log("Have them configured as follows:")
  log("totaldeleted - Create empty file if running for first time.")
  log("banned_users - Create empty file if running for first time. Bot will add banned users automatically. Add manually on separate lines.")
 
### Load saved data
try:
  banned_users = r.get_info(thing_id=banned_users_comment).body.split()
  deleted = 0
  success("DATA LOADED")
except:
  file_warning()
  traceback.print_exc()
  exit()

while True:
  try:
    log("COMMENT SCORE CHECK CYCLE STARTED")
    user = r.get_redditor(USERNAME)
    total = 0
    upvoted = 0
    unvoted = 0
    downvoted = 0
    for c in user.get_comments(limit=None):
      
      if len(str(c.score)) == 4:
	spaces = ""
      if len(str(c.score)) == 3:
	spaces = " "
      if len(str(c.score)) == 2:
	spaces = "  "
      if len(str(c.score)) == 1:
	spaces = "   "
      
      total = total + 1
      if c.score < 1:
	c.delete()
	print "\033[1;41m%s%s\033[1;m"%(spaces,c.score),
	deleted = deleted + 1
	downvoted = downvoted + 1
      elif c.score > 10:
	print "\033[1;32m%s%s\033[1;m"%(spaces,c.score),
	upvoted = upvoted + 1
      elif c.score > 1:
	print "\033[1;34m%s%s\033[1;m"%(spaces,c.score),
	upvoted = upvoted + 1
      elif c.score > 0:
	print "\033[1;30m%s%s\033[1;m"%(spaces,c.score),
	unvoted = unvoted + 1
      
    print ("")
    log("COMMENT SCORE CHECK CYCLE COMPLETED")
    urate = round(upvoted / float(total) * 100)
    nrate = round(unvoted / float(total) * 100)
    drate = round(downvoted / float(total) * 100)
    warn("Upvoted:      %s\t%s\b\b %%"%(upvoted,urate))
    warn("Unvoted       %s\t%s\b\b %%"%(unvoted,nrate))
    warn("Downvoted:    %s\t%s\b\b %%"%(downvoted,drate))
    warn("Total:        %s"%total)

    ### Check inbox few times
    log("AUTODELETE CYCLES STARTED")
    for x in range(1, 11):
      log("CYCLE %s"%x)
      try:
	unread = r.get_unread(limit=None)
	for msg in unread:
	  ### Remove comment 
	  if re.search(deletekeyword, msg.body.lower()) or re.search("\+remove", msg.body.lower()): #remove "+remove" for new bot username
	    try:
	      bot_comment_id = msg.parent_id
	      bot_comment = r.get_info(thing_id=bot_comment_id)
	      bot_comment_parent = r.get_info(thing_id=bot_comment.parent_id)
	      if bot_comment.author.name == USERNAME:
		if msg.author.name == bot_comment_parent.author.name or int(time.strftime("%s")) - int(c.created) > 86400:
		  bot_comment.delete()
		  deleted = deleted + 1
		  success("AUTODELETION AT %s"%bot_comment_parent.permalink)
		else:
		  #msg.reply ("*Sorry. Only /u/%s can trigger this delete.*"%bot_comment_parent.author.name)
		  fail("BAD AUTODELETE REQUEST AT %s"%bot_comment_parent.permalink)
	      else:
		if msg.author.name != USERNAME:
		  warn("AUTODELETE FLAG OUT OF CONTEXT AT %s"%bot_comment_parent.permalink)
	      msg.mark_as_read()
	    except Exception as e:
	      if (str(e)=="'NoneType' object has no attribute 'name'"):
		bot_comment.delete()
		deleted = deleted + 1
		success("AUTODELETION (ORPHAN) AT %s"%bot_comment_parent.permalink)
	      else:
		fail("%s\033[1;m"%e)
	      msg.mark_as_read()
	      continue

	  ### Add user to exclude list
	  if re.search(excludekeyword, msg.body.lower()):
	    banned_users = r.get_info(thing_id=banned_users_comment).body.split()
	    banned_users.append(msg.author.name)
	    banned_users.sort()
	    c_banned_users = ""
	    for item in banned_users:
	      c_banned_users = item+"\n"+c_banned_users
	    c_banned_users.strip()
	    r.get_info(thing_id=banned_users_comment).edit(c_banned_users)
	    time.sleep(1)
	    msg.mark_as_read()
	    msg.reply("*Done! I won't reply to your comments (in effect 60 minutes after this comment).*\n\n*Have a nice day!*")
	    
	    success("BANNED /u/%s AT %s"%(msg.author.name,msg.id))
	    
	  if re.search(includekeyword, msg.body.lower()):
	    msg.mark_as_read()
	    banned_users = r.get_info(thing_id=banned_users_comment).body.split()
	    if msg.author.name in banned_users:
	      banned_users.remove(str(msg.author.name))
	      r.get_info(thing_id=banned_users_comment).edit(banned_users)
	      msg.reply("*OK! I removed you from the blacklist. I will resume replying to your comments now.*")
	      success("UNBANNED /u/%s AT %s"%(msg.author.name,msg.permalink))
	    else:
	      msg.reply("*Dear, you are not in the blacklist.*")
	      warn("BAD UNBAN REQUEST BY /u/%s AT %s"%(msg.author.name,msg.permalink))

	time.sleep(60)
      except Exception as e:
	traceback.print_exc()
	fail(e)
	time.sleep(60)
	continue
    log("AUTODELETE CYCLES COMPLETED")
        
  except KeyboardInterrupt:
    log("EXITING")
    break
  except Exception as e:
    #traceback.print_exc()
    fail(e)
    time.sleep(3)
    continue
  
