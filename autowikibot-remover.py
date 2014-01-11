# -*- coding: utf-8 -*-
import praw, time, re, pickle, traceback, os, memcache
from util import success, warn, log, fail

### Set root directory to script directory
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

### Set memcache client
shared = memcache.Client(['127.0.0.1:11211'], debug=0)

r = praw.Reddit("autowikibot by /u/acini at /r/autowikibot")
deletekeyword = "delete"
excludekeyword = "leave me alone"
global banned_users

def file_warning():
  fail("One or more of data files is not found or is corrupted.")
  log("Have them configured as follows:")
  log("totaldeleted - Create empty file if running for first time.")
  log("banned_users - Create empty file if running for first time. Bot will add banned users automatically. Add manually on separate lines.")
 
### Load saved data
try:
  banned_users = [line.strip() for line in open('banned_users')]
  shared.set('banned_users',banned_users)
  with open('totaldeleted') as f: #TODO replace pickle
      deleted = pickle.load(f)
  with open ('userpass', 'r') as myfile:
    lines=myfile.readlines()
  success("DATA LOADED")
except:
  file_warning()
  exit()



### Login
USERNAME = lines[0].strip()
PASSWORD = lines[1].strip()

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
      if c.score < 0:
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
	#call (["firefox",c.permalink])
      elif c.score > 0:
	print "\033[1;30m%s%s\033[1;m"%(spaces,c.score),
	unvoted = unvoted + 1
      elif c.score < 1:
	print "\033[1;33m%s%s\033[1;m"%(spaces,c.score),
	downvoted = downvoted + 1
      
    print ("")
    log("COMMENT SCORE CHECK CYCLE COMPLETED")
    urate = round(upvoted / float(total) * 100)
    nrate = round(unvoted / float(total) * 100)
    drate = round(downvoted / float(total) * 100)
    warn("Upvoted:      %s\t%s\b\b %%"%(upvoted,urate))
    warn("Unvoted       %s\t%s\b\b %%"%(unvoted,nrate))
    warn("Downvoted:    %s\t%s\b\b %%"%(downvoted,drate))
    warn("Total:        %s"%total)
    
    with open('totaldeleted', 'w') as f:
      pickle.dump(deleted, f)
    log("STATISTICS SAVED")
    
    

    ### Check inbox 15 times
    log("AUTODELETE CYCLES STARTED")
    for x in range(1, 6):
      log("CYCLE %s"%x)
      try:
	unread = r.get_unread(limit=None)
	for msg in unread:
	  ### Remove comment 
	  if re.search(deletekeyword, msg.body.lower()) or re.search("\+remove", msg.body.lower()): #remove "+remove" for new bot username
	    try:
	      bot_comment_id = msg.parent_id
	      bot_comment = r.get_info(thing_id=bot_comment_id)
	      if bot_comment.author.name == USERNAME:
		bot_comment_parent = r.get_info(thing_id=bot_comment.parent_id)
		if msg.author.name == bot_comment_parent.author.name:
		  bot_comment.delete()
		  deleted = deleted + 1
		  success("AUTODELETION AT %s"%bot_comment_parent.permalink)
		else:
		  #msg.reply ("*Sorry. Only /u/%s can trigger this delete.*"%bot_comment_parent.author.name)
		  fail("BAD AUTODELETE REQUEST AT /u/%s"%bot_comment_parent.permalink)
	      else:
		if msg.author.name != USERNAME:
		  warn("AUTODELETE FLAG OUT OF CONTEXT AT %s"%bot_comment_parent.permalink)
		  continue
	      msg.mark_as_read()
	    except Exception as e:
	      if (str(e)=="'NoneType' object has no attribute 'name'"):
		bot_comment.delete()
		deleted = deleted + 1
		success("AUTODELETION (ORPHAN) AT %s"%bot_comment_parent.permalink)
	      else:
		fail("%s\033[1;m"%e)
	      #msg.mark_as_read()
	      continue
	  else:
	    msg.mark_as_unread()
	  ### Add user to exclude list ###TODO remove user from exclusion list
	  if re.search(excludekeyword, msg.body.lower()):
	    with open('banned_users', 'a') as myfile:
	      myfile.write("%s\n"%msg.author.name)
	    msg.mark_as_read()
	    msg.reply("*Done! I won't reply to your comments now.*\n\n*Have a nice day!*")
	    ### Save user to array and communicate to commenter process
	    try:
	      banned_users = [line.strip() for line in open('banned_users')] #redundancy if banned user is manually added
	    except:
	      file_warning()
	    shared.set('banned_users',banned_users)
	    banned_users.append(msg.author.name)
	    shared.set('banned_users',banned_users)
	    success("BANNED /u/%s AT %s"%(msg.author.name,bot_comment.permalink))
	  time.sleep(1)
	time.sleep(30)
      except KeyboardInterrupt:
	with open('totaldeleted', 'w') as f:
	  pickle.dump(deleted, f)
	success("STATISTICS DUMPED TO FILE")
	exit()
      except Exception as e:
	traceback.print_exc()
	fail(e)
	time.sleep(60)
	continue
    log("AUTODELETE CYCLES COMPLETED")
    with open('totaldeleted', 'w') as f:
      pickle.dump(deleted, f)
    success("DATA SAVED")
        
  except KeyboardInterrupt:
    with open('totaldeleted', 'w') as f:
	pickle.dump(deleted, f)
    success("DATA SAVED")
    log("EXITING")
    break
  except Exception as e:
    #traceback.print_exc()
    fail(e)
    time.sleep(3)
    continue
  