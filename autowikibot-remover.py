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
excludekeyword = "leave me alone"
includekeyword = "follow me again"
global banned_users

### Login
with open ('datafile.inf', 'r') as myfile:
    datafile_lines=myfile.readlines()
USERNAME = datafile_lines[0].strip()
PASSWORD = datafile_lines[1].strip()

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

### Load saved data
try:
  banned_users_page = r.get_wiki_page('autowikibot','userblacklist')
  banned_users = banned_users_page.content_md.strip().split()
  deleted = 0
  success("DATA LOADED")
except Exception as e:
  fail(e)
  #traceback.print_exc()
  exit()

  
  
while True:
  try:
    
    ### Check inbox few times
    log("AUTODELETE CYCLES STARTED")
    for x in range(1, 11):
      log("CYCLE %s"%x)
      try:
	unread = r.get_unread(limit=None)
	for msg in unread:
	  
	  if re.search(r'\+delete\s', msg.body.lower()):
	    try:
	      id = re.findall(r'\+delete\s(.*?)$',msg.body.lower())[0]
	      id = 't1_'+id
	      comment = r.get_info(thing_id=id)
	      comment_parent = r.get_info(thing_id=comment.parent_id)
	      
	      
	      if msg.author.name == comment_parent.author.name or msg.author.name == 'acini':
		comment.delete()
		deleted+=1
		#msg.reply('I have deleted [my comment]('+comment.permalink+'), which was reply to your [this comment]('+comment_parent.permalink+').\n\nHave an amazing day, '+str(msg.author.name)+'!\n\n-AutoWikibot')
		success("DELETION AT %s"%comment_parent.id)
		msg.mark_as_read()
	      else:
		#msg.reply('Oops, only /u/'+str(comment_parent.author.name)+' can delete that [comment]('+comment.permalink+'). Downvote the comment if you think it is not helping.\n\nHave an amazing day, '+str(msg.author.name)+'!\n\n-AutoWikibot')
		fail("BAD DELETE REQUEST BY /u/%s"%str(msg.author.name))
		msg.mark_as_read()
	      continue
	    except Exception as e:
	      if (str(e)=="'NoneType' object has no attribute 'name'"):
		comment.delete()
		deleted+=1
		#msg.reply('[My comment]('+comment.permalink+') which was reply to [this comment]('+comment_parent.permalink+') is also found orphan. I have deleted it as requested.\n\nHave an amazing day, '+str(msg.author.name)+'!\n\n-AutoWikibot')
		success("DELETION (ORPHAN) AT %s"%comment_parent.id)
	      else:
		fail("%s\033[1;m"%e)
	      msg.mark_as_read()
	      continue
	  
	  if re.search(r'\+toggle-nsfw\s', msg.body.lower()):
	    try:
	      id = re.findall(r'\+toggle-nsfw\s(.*?)$',msg.body.lower())[0]
	      id = 't1_'+id
	      comment = r.get_info(thing_id=id)
	      comment_parent = r.get_info(thing_id=comment.parent_id)
	      
	      
	      if msg.author.name == comment_parent.author.name or msg.author.name == 'acini':
		if '[](#nsfw-toggled)' in comment.body.lower():
		  #msg.reply('Sorry, NSFW can be toggled only once for a particular comment.')
		  msg.mark_as_read()
		  continue
		
		elif '[](#nsfw-start)' in comment.body.lower():
		  nsfwstate = 'OFF'
		  nsfwurl = "http://www.reddit.com/message/compose?to=%28This%20is%20a%20placeholder%29&subject=NSFW%20toggled:&message=NSFW%20was%20toggled%20"+nsfwstate+"%20by%20parent%20commenter%20for%20this%20comment."
		  nsfwtag = " [](#sfw)[](#nsfw-toggled)"
		  replacedb = re.sub(r'\[\]\(\#nsfw-start\).*?\[\]\(\#nsfw-end\)',nsfwtag,comment.body).replace('&amp;','&').replace('&gt;','>').replace('^toggle ^NSFW','').replace('^or[](#or)','')
		  
		elif '[](#sfw)' in comment.body.lower():
		  nsfwstate = 'ON'
		  nsfwurl = "http://www.reddit.com/message/compose?to=%28This%20is%20a%20placeholder%29&subject=NSFW%20toggled:&message=NSFW%20was%20toggled%20"+nsfwstate+"%20by%20parent%20commenter%20for%20this%20comment."
		  nsfwtag = " [](#nsfw-start)**^NSFW** [^^(?)]("+nsfwurl+")[](#nsfw-end)[](#nsfw-toggled)"
		  replacedb = comment.body.replace('[](#sfw)',nsfwtag).replace('&amp;','&').replace('&gt;','>').replace('^toggle ^NSFW','').replace('^or[](#or)','')
		
		comment.edit(replacedb)
		##msg.reply('NSFW was toggled **'+nsfwstate+'** for [this comment]('+comment.permalink+').\n\nHave an amazing day, '+str(msg.author.name)+'!\n\n-AutoWikibot')
		success("NSFW TOGGLE AT %s"%comment_parent.id)
		msg.mark_as_read()
	      else:
		##msg.reply('Oops, only /u/'+str(comment_parent.author.name)+' can toggle NSFW for that [comment]('+comment.permalink+'). \n\nHave an amazing day, '+str(msg.author.name)+'!\n\n-AutoWikibot')
		fail("BAD NSFW TOGGLE REQUEST BY /u/%s"%str(msg.author.name))
		msg.mark_as_read()
	      continue
	    except Exception as e:
	      if (str(e)=="'NoneType' object has no attribute 'name'"):
		comment.delete()
		deleted+=1
		##msg.reply('[My comment]('+comment.permalink+') which was reply to [this comment]('+comment_parent.permalink+') is also found orphan. I have deleted it as requested.\n\nHave an amazing day, '+str(msg.author.name)+'!\n\n-AutoWikibot')
		success("DELETION (ORPHAN) AT %s"%comment_parent.id)
	      else:
		fail("%s\033[1;m"%e)
	      msg.mark_as_read()
	      continue
	  ### Add user to exclude list
	  if re.search(excludekeyword, msg.body.lower()):
	    banned_users = banned_users_page.content_md.strip().split()
	    banned_users.append(msg.author.name)
	    banned_users.sort()
	    banned_users = list(set(banned_users))
	    banned_users.sort(reverse=True)
	    c_banned_users = ""
	    for item in banned_users:
	      c_banned_users = "    "+item+'\n'+c_banned_users
	    editsummary = 'added '+str(msg.author.name)
	    r.edit_wiki_page('autowikibot','userblacklist',c_banned_users,editsummary)
	    time.sleep(1)
	    msg.mark_as_read()
	    #msg.reply("*Done! I won't reply to your comments now. Allow me 15 minutes to put this in effect.*\n\n*Have a nice day!*")
	    
	    success("BANNED /u/%s AT %s"%(msg.author.name,msg.id))
	    
	  if re.search(includekeyword, msg.body.lower()):
	    msg.mark_as_read()
	    banned_users = banned_users_page.content_md.strip().split()
	    if msg.author.name in banned_users:
	      banned_users.remove(str(msg.author.name))
	      banned_users = list(set(banned_users))
	      banned_users.sort(reverse=True)
	      c_banned_users = ""
	      for item in banned_users:
		c_banned_users = "    "+item+'\n'+c_banned_users
	      editsummary = 'removed '+str(msg.author.name)
	      r.edit_wiki_page('autowikibot','userblacklist',c_banned_users,editsummary)
	      #msg.reply("*OK! I removed you from the blacklist. I will resume replying to your comments now.*")
	      success("UNBANNED /u/%s AT %s"%(msg.author.name,msg.id))
	    else:
	      #msg.reply("*Dear, you are not in the blacklist.*")
	      warn("BAD UNBAN REQUEST BY /u/%s AT %s"%(msg.author.name,msg.id))
	      
	log('Sleeping')
	time.sleep(60)
      except Exception as e:
	traceback.print_exc()
	fail(e)
	time.sleep(60)
	continue
    log("AUTODELETE CYCLES COMPLETED")
    
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
      if c.score < 1 or '#placeholder-awb' in c.body.lower:
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
        
  except KeyboardInterrupt:
    log("EXITING")
    break
  except Exception as e:
    #traceback.print_exc()
    fail(e)
    time.sleep(3)
    continue
  
