# -*- coding: utf-8 -*-
### TODO integrate wikipedia with url_string extraction

import praw, time, datetime, re, urllib, urllib2, pickle, pyimgur, os, traceback, memcache, wikipedia, string
from util import success, warn, log, fail, special, bluelog
from bs4 import BeautifulSoup
from HTMLParser import HTMLParser
### Uncomment to debug
#import logging
#logging.basicConfig(level=logging.DEBUG)

### Set memcache client
shared = memcache.Client(['127.0.0.1:11211'], debug=0)

### Set root directory to script directory
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

### functions
class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()

def reddify(html):
  html = html.replace('<b>', '**')
  html = html.replace('</b>', '**')
  html = re.sub('<sup>','^',html)
  html = re.sub('<sup.*?>','',html)
  html = html.replace('</sup>', '')
  #html = html.replace('<i>', '*')
  #html = html.replace('</i>', '*')
  return html

def strip_wiki(wiki):
  wiki = re.sub('\[.*?\]','',wiki)
  wiki = re.sub("\( listen\)", '', wiki)
  return wiki

def split_by_length(s,block_size):
    w=[]
    n=len(s)
    for i in range(0,n,block_size):
        w.append(s[i:i+block_size])
    return w
  
def process_brackets_links(string):
  string = ("%s)"%string)
  string = string.replace("\\", "")
  return string

def process_brackets_syntax(string):
  string = string.replace("\\", "")
  string = ("%s\)"%string)
  return string
  
def file_warning():
  fail("One or more of data files is not found or is corrupted.")
  log("Have them configured as follows:")
  log("already_done_dump - Create empty file if running for first time.")
  log("totalposted - Create empty file if running for first time.")
  log("badsubs - Create empty file if running for first time. Add excluded subreddits if you are using \"all\" as allowed subreddit. Leave empty if allowing specific subreddits.")
  log("banned_users - Create empty file if running for first time. Bot will add banned users automatically. Add manually on separate lines.")
  log("imgur_client_id - Put your imgur client_id in that file")
  
def load_data(): #TODO load allowed subreddits
  try:
    global banned_users
    banned_users = [line.strip() for line in open('banned_users')]
    global badsubs
    badsubs = [line.strip() for line in open('badsubs')]
    global already_done
    already_done = [line.strip() for line in open('already_done_dump')]
    with open('totalposted') as f:   #TODO replace pickle with simple write store in one file called stats
      global totalposted
      totalposted = pickle.load(f)
    with open ('imgur_client_id', 'r') as myfile:
      global imgur_client_id
      imgur_client_id=myfile.read()
    with open ('userpass', 'r') as myfile:
      global userpass_lines
      userpass_lines=myfile.readlines()
    success("DATA LOADED")
  except:
    file_warning()
    exit()

def save_changing_variables():
  banned_users.sort()
  with open('banned_users', 'w+') as myfile:
    for item in banned_users:
      myfile.write("%s\n" % item)
  badsubs.sort()
  with open('badsubs', 'w+') as myfile:
    for item in badsubs:
      myfile.write("%s\n" % item)
  with open('already_done_dump', 'w+') as myfile:
    for item in already_done:
      myfile.write("%s\n" % item)
  with open('totalposted', 'w') as f:#TODO replace pickle with simple write
    pickle.dump(totalposted, f)
  success("DATA SAVED")

  
### declare variables
load_data()
r = praw.Reddit("autowikibot by /u/acini at /r/autowikibot")
im = pyimgur.Imgur(imgur_client_id)
linkWords = ['://en.wikipedia.org/wiki/', '://en.m.wikipedia.org/wiki/']
endoflinkWords = ['\n', ' ']
pagepropsdata = ""
  
### Login
USERNAME = userpass_lines[0].strip()
PASSWORD = userpass_lines[1].strip()

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
	  fail("%s"%e)
	  time.sleep(5)
	
while True:
  try:
    #comments = r.get_comments("all",limit = 1000)
    #for post in comments:
    for post in praw.helpers.comment_stream(r,'all', limit = None):
      ### check if comment is already processed, skip if it is
      if post.id in already_done:
	#warn("Previously processed")
	continue
      if (post.author.name == USERNAME):
	already_done.append(post.id)
	#warn("My comment")
	continue
      ### check if comment is by banned user, skip if it is
      if post.author.name in banned_users:
	already_done.append(post.id)
	#warn("Banned user")
	continue
      
      ### Proceed with processing as minumum criteria are satisfied.
      already_done.append(post.id)
	
      ### check if there is wikibot call
      #define_call = bool(re.search("wikibot.*?define",post.body.lower()))
      #if define_call:
	#already_done.append(post.id)
	#log("__________________________________________________")
	#special("DEFINITION CALL: %s"%post.permalink)
	#post_body = re.sub('wikibot.*?define ','__BODYSPLIT__',post.body.lower())
	#post_body = re.sub('\?','',post_body)
	#term = post_body.split('__BODYSPLIT__')[1]
	#try:
	  #term = term.split('\n')[0]
	#except:
	  #log("COULD NOT SPLIT")
	  #pass
	#log("TERM: %s"%term)
	#try:
	  #definition_text = wikipedia.summary(term,sentences=1,auto_suggest=False,redirect=True)
	  #if definition_text.__len__() < 200:
	    #definition_text = wikipedia.summary(term,sentences=2,auto_suggest=False,redirect=True)
	  #definition_link = wikipedia.page(term,auto_suggest=False).url
	  #title = wikipedia.page(term,auto_suggest=False).title
	  #if bool(re.search(title,definition_text)):
	    #definition = re.sub(title,"[**"+title+"**]("+definition_link+")",definition_text)
	  #else:
	    #definition = "[**"+title+"**](" + definition_link + "): " + definition_text
	  #log("INTERPRETATION: %s"%filter(lambda x: x in string.printable, title))
	  #comment = "*Here you go:*\n\n---\n\n>"+definition+"\n\n---\n\n[^(about)](http://www.reddit.com/r/autowikibot/wiki/index) ^| *^(/u/"+post.author.name+" can reply with 'delete'. Will also delete if comment's score is -1 or less.)*  ^| [^(**call me**: wikibot, what is something?)](http://www.reddit.com/r/autowikibot/wiki/commandlist)"
	#except Exception as e:
	  #if bool(re.search('.*may refer to:.*',filter(lambda x: x in string.printable, e))):
	    #deflist = ""
	    #for idx, val in enumerate(str(e).split('may refer to: \n')[1].split('\n')):
	      #deflist = deflist + "\n\n>" + wikipedia.summary(str(e).split('may refer to: \n')[1].split('\n')[idx],auto_suggest=True,sentences=1)
	    #comment = "*Can you be a little specific, please?*\n\n---\n\n>\n"+str(e).replace('\n','\n\n>')+"\n\n---"+deflist+"\n\n---\n\n[^(about)](http://www.reddit.com/r/autowikibot/wiki/index) ^| *^(/u/"+post.author.name+" can reply with 'delete'. Will also delete if comment's score is -1 or less.)*  ^| [^(**call me**: wikibot, what is something?)](http://www.reddit.com/r/autowikibot/wiki/commandlist)"
	    #log("ASKING FOR DISAMBIGUATION")
	  #else:
	    #log("INTERPRETATION FAIL: %s"%filter(lambda x: x in string.printable, term))
	    #try:
	      #term = wikipedia.search(term,results=1)[0]
	      #definition_text = wikipedia.summary(term,sentences=1,auto_suggest=False,redirect=True)
	      #if definition_text.__len__() < 200:
		#definition_text = wikipedia.summary(term,sentences=2,auto_suggest=False,redirect=True)
	      #definition_link = wikipedia.page(term,auto_suggest=False).url
	      #definition_link = definition_link.replace(')','\)')
	      #title = wikipedia.page(term,auto_suggest=False).title
	      #if bool(re.search(title,definition_text)):
		#definition = re.sub(title,"[**"+title+"**]("+definition_link+")",definition_text)
	      #else:
		#definition = "[**"+title+"**](" + definition_link + "): " + definition_text
	      #comment = "*You mean,* **"+term+"**?\n\n---\n\n>"+definition+"\n\n---\n\n[^(about)](http://www.reddit.com/r/autowikibot/wiki/index) ^| *^(/u/"+post.author.name+" can reply with 'delete'. Will also delete if comment's score is -1 or less.)*  ^| [^(**call me**: wikibot, what is something?)](http://www.reddit.com/r/autowikibot/wiki/commandlist)"
	      #log("SUGGESTING %s"%term)
	    #except:
	      #trysentence = wikipedia.summary(val,auto_suggest=True,sentences=1)
	      #comment = "*" + term + "?*\n\n---\n\n"+trysentence+"\n\n---\n\n[^(about)](http://www.reddit.com/r/autowikibot/wiki/index) ^| *^(/u/"+post.author.name+" can reply with 'delete'. Will also delete if comment's score is -1 or less.)*  ^| [^(**call me**: wikibot, what is something?)](http://www.reddit.com/r/autowikibot/wiki/commandlist)"
	      #log("COULD NOT SUGGEST FOR %s"%term)
	    #try:
	      #post.reply(comment)
	      #totalposted = totalposted + 1
	      #success("#%s REPLY SUCCESSFUL"%totalposted)
	    #except Exception as e:
	      #warn("REPLY FAILED: %s @ %s"%(e,post.subreddit))# TODO add to badsubs on 403
	    #continue
	#try:
	  #post.reply(comment)
	  #totalposted = totalposted + 1
	  #success("#%s CALL REPLY SUCCESSFUL"%totalposted)
	#except Exception as e:
	  #warn("CALL REPLY: %s @ %s"%(e,post.subreddit))# TODO add to badsubs on 403
	##continue
      
      ### check if comment has links quotes or is previously processed
      tell_me_call = bool(re.search("wikibot.*?tell .*? about",post.body.lower()))
      what_is_call = bool(re.search("wikibot.*?wh.*? (is|are)",post.body.lower()))
      has_link = any(string in post.body for string in linkWords)
      if has_link or tell_me_call or what_is_call:
	### check comment body quotes, skip if present
	if re.search(r"&gt;", post.body) and not tell_me_call and not what_is_call:
	  already_done.append(post.id)
	  #warn("Has quote")
	  continue
	### check comment body for more than one wikipedia link, skip if present
	if re.search(r"wikipedia.org/wiki/.*wikipedia.org/wiki/", post.body, re.DOTALL):
	  already_done.append(post.id)
	  #warn("Has second link") 
	  continue
	### check if comment is bot's own post, skip if it is
	
	### check if comment is from excluded subreddit, skip if it is
	sub = post.subreddit
	sublower = str(sub).lower()
	if sublower in badsubs:
	  #warn("Excluded sub")
	  continue
	
	### process url string
	try:
	  after_split = post.body.split("wikipedia.org/wiki/")[1]
	  ### Seprate url string from mistakenly put characters in front of it (commenter mistake)
	  if re.search(r'\)#',after_split):
	    for e in endoflinkWords:
	      after_split = after_split.split(e)[0]
	  else:
	    for e in endoflinkWords:
	      after_split = after_split.split(e)[0]
	    after_split = after_split.split(")")[0]
	except:
	  pass
	
	### If it is call for summary, pass variable to summary processor
	log("__________________________________________________")
	if tell_me_call or what_is_call:
	  special("SUMMARY CALL: %s"%post.permalink)
	  bit_comment_start = "A summary from "
	  if tell_me_call:
	    post_body = re.sub('wikibot.*?tell .*? about','__BODYSPLIT__',post.body.lower())
	  else:
	    post_body = re.sub('wikibot.*?wh.*? (is|are) ','__BODYSPLIT__',post.body.lower())
	  term = post_body.split('__BODYSPLIT__')[1]
	  term = re.sub('\?','',term)
	  try:
	    term = term.split('\n')[0]
	  except:
	    log("COULD NOT SPLIT")
	    pass
	  log("TERM: %s"%filter(lambda x: x in string.printable, term))
	  try:
	    title = wikipedia.page(term,auto_suggest=False).title
	    after_split = title
	    log("INTERPRETATION: %s"%filter(lambda x: x in string.printable, title))
	  except Exception as e:  
	    if bool(re.search('.*may refer to:.*',filter(lambda x: x in string.printable, str(e)))):
	      deflist = ""
	      for idx, val in enumerate(filter(lambda x: x in string.printable, str(e)).split('may refer to: \n')[1].split('\n')):
		deflist = deflist + "\n\n>" + wikipedia.summary(val,auto_suggest=True,sentences=1)
		if idx > 3:
		  break
	      summary = "*Can you be a little specific, please? There's too many of "+term.strip()+"*\n\n---\n\n>\n"+str(e).replace('\n','\n\n>')+"\n\n---"+deflist+"\n\n---\n\n[^(about)](http://www.reddit.com/r/autowikibot/wiki/index) ^| *^(/u/"+post.author.name+" can reply with 'delete'. Will also delete if comment's score is -1 or less.)*  ^| [^(**call me**: wikibot, what is something?)](http://www.reddit.com/r/autowikibot/wiki/commandlist) ^| [^(flag for glitch)](http://www.reddit.com/message/compose?to=acini&subject=bot%20glitch&message=%0Acontext:"+post.permalink+")"
	      log("ASKING FOR DISAMBIGUATION")
	    else:
	      log("INTERPRETATION FAIL: %s"%filter(lambda x: x in string.printable, term))
	      try:
		suggest = wikipedia.search(term,results=1)[0]
		summary = wikipedia.summary(suggest,auto_suggest=False,redirect=True)
		suggest_link = wikipedia.page(suggest).url
		suggest_link = suggest_link.replace(')','\)')
		suggest_with_link = "["+suggest+"]("+suggest_link+")"
		summary = "*You mean,* **"+suggest_with_link+"**? *It's the closest match I could find.*\n\n---\n\n>"+summary+"\n\n---\n\n[^(about)](http://www.reddit.com/r/autowikibot/wiki/index) ^| *^(/u/"+post.author.name+" can reply with 'delete'. Will also delete if comment's score is -1 or less.)*  ^| [^(**call me**: wikibot, what is something?)](http://www.reddit.com/r/autowikibot/wiki/commandlist)"
		log("SUGGESTING %s"%filter(lambda x: x in string.printable, suggest))
	      except:
		trialsummary = wikipedia.summary(term,auto_suggest=True)
		summary = "*" + term.strip() + "? I found this closest match:*\n\n---\n\n"+trialsummary+"\n\n---\n\n[^(about)](http://www.reddit.com/r/autowikibot/wiki/index) ^| *^(/u/"+post.author.name+" can reply with 'delete'. Will also delete if comment's score is -1 or less.)*  ^| [^(**call me**: wikibot, what is something?)](http://www.reddit.com/r/autowikibot/wiki/commandlist)"
		log("COULD NOT SUGGEST FOR %s"%filter(lambda x: x in string.printable, term))  
	    try:
	      post.reply(summary)
	      totalposted = totalposted + 1
	      success("#%s REPLY SUCCESSFUL"%totalposted)
	    except Exception as e:
	      warn("REPLY FAILED: %s @ %s"%(e,post.subreddit))# TODO add to badsubs on 403
	    continue
	else:
	  log("LINK TRIGGER: %s"%post.permalink)
	  bit_comment_start = "Here's a bit from linked "
	
	url_string = after_split
	url_string_for_fetch = url_string.replace('_', '%20')
	url_string_for_fetch = url_string.replace(' ', '%20')
	article_name = url_string.replace('_', ' ')
	
	### url string correction for brackets
	if re.search(r"[(]", url_string_for_fetch):
	  url_string_for_fetch = process_brackets_links(url_string_for_fetch)
	  if not re.search(r"[(]", url_string_for_fetch):
	    article_name = ("%s)"%article_name)
	  url_string = process_brackets_syntax(url_string)
	
	
	### In case user comments like "/wiki/Article.", remove last 1 letter
	if url_string_for_fetch.endswith(".") or url_string_for_fetch.endswith("]"):
	  url_string_for_fetch = url_string_for_fetch[0:--(url_string_for_fetch.__len__()-1)]
	
	### check for subheading in url string, skip if present #TODO process subheading requests
	if re.search(r"#",article_name) and not what_is_call and not tell_me_call:
	  pagename = article_name.split('#')[0]
	  if re.search('\)',pagename):
	    pagename = process_brackets_links(pagename)
	  pagename = urllib.unquote(pagename)
	  sectionname = article_name.split('#')[1]
	  if re.search('\)',sectionname):
	    sectionname = sectionname.replace(')','')
	    sectionname = sectionname.replace('\\','')
	  sectionname = sectionname.strip().replace('.','%')
	  sectionname = urllib.unquote(sectionname)
	  bluelog("TOPIC: %s"%filter(lambda x: x in string.printable, pagename))
	  bluelog("LINKS TO SECTION: %s"%filter(lambda x: x in string.printable, sectionname))
	  try:
	    page = wikipedia.page(pagename.encode('utf-8','ignore'))
	    section = page.section(sectionname.encode('utf-8','ignore'))
	    if section == None or str(section.encode('utf-8','ignore')).strip() == "":
	      raise Exception("SECTION RETURNED EMPTY")
	    sectionname = sectionname.replace('_',' ')
	    link = page.url+"#"+sectionname
	    link = link.replace(')','\)')
	    page_url = page.url.replace(')','\)')
	    section = section.replace('\n','\n\n>')
	    success("TEXT PACKAGED")
	    if section.__len__() > 3000:
	      log("SECTION CUT AT 3000 CHARACTERS")
	      section = split_by_length(section,3000)[0]+" ... \n\n`(Section too large, cut at 3000 characters)`"
	    comment = ("*Here's the linked section ["+sectionname+"]("+link+") from Wikipedia article ["+page.title+"]("+page_url+")* : \n\n---\n\n>"+section+"\n\n---\n\n[^(about)](http://www.reddit.com/r/autowikibot/wiki/index) ^| *^(/u/"+post.author.name+" can reply with 'delete'. Will also delete if comment's score is -1 or less.)*  ^| [^(**call me**: wikibot, what is something?)](http://www.reddit.com/r/autowikibot/comments/1ux484/ask_wikibot/)")
	    try:
	      post.reply(comment)
	      totalposted = totalposted + 1
	      success("#%s REPLY SUCCESSFUL"%totalposted)
	    except Exception as e:
	      warn("REPLY FAILED: %s @ %s"%(e,post.subreddit))# TODO add to badsubs on 403
	  except Exception as e:
	    traceback.print_exc()
	    warn("SECTION PROCESSING: %s"%e)
	    continue
	  continue
	
	### check if link is wikipedia namespace, skip if present
	has_hash = re.search(r":",article_name) and not re.search(r": ",article_name)
	if has_hash and not what_is_call and not tell_me_call:
	  log("Namespace link")
	  continue

	### check if article is a list, skip if it is
	if re.search(r"List of.*",article_name) and not tell_me_call and not what_is_call:
	  log("Is a list")
	  continue
	
	### fetch data from wikipedia
	
	url = ("http://en.wikipedia.org/w/api.php?action=query&titles="+url_string_for_fetch+"&prop=pageprops&format=xml")
	try:
	  pagepropsdata = urllib2.urlopen(url).read()
	  pagepropsdata = pagepropsdata.decode('utf-8','ignore')
	  ppsoup = BeautifulSoup(pagepropsdata)
	  article_name_terminal = ppsoup.page['title']
	except:
	  try:
	    article_name_terminal = article_name.replace('\\', '')
	  except:
	    article_name_terminal = article_name.replace('\\', '').decode('utf-8','ignore')
	
	log("TOPIC: %s"%article_name_terminal.encode('utf-8','ignore'))
	url = ("http://en.wikipedia.org/w/api.php?action=parse&page="+url_string_for_fetch+"&format=txt&prop=text&section=0&redirects")
	try:
	  sectiondata = urllib2.urlopen(url).read()
	  sectiondata = sectiondata.decode('utf-8','ignore')
	  sectiondata = reddify(sectiondata)
	  soup = BeautifulSoup(sectiondata)
	  globalsoup = soup
	except Exception as e:
	  fail("FETCH: %s"%e)
	  continue
	
	

	### Delete any tables, remove coordinates, cite error
	while soup.table:
	  discard = soup.table.extract()
	while soup.find(id='coordinates'):
	  discard = soup.find(id='coordinates').extract()
	while soup.find("strong", { "class" : "error mw-ext-cite-error" }):
	  discard = soup.find("strong", { "class" : "error mw-ext-cite-error" }).extract()
	while soup.find("sup", { "class" : "reference" }):
	  discard = soup.find("sup", { "class" : "reference" }).extract()
	while soup.find("span", { "class" : "t_nihongo_help noprint" }):
	  discard = soup.find("span", { "class" : "t_nihongo_help noprint" }).extract()
	
	### extract paragraph
	### <!-- is used as ending because it is present with every api fetch
	### Replace <!-- with </p> to get only first paragraph instead of full introduction
	### Not using xml parsing because tables etc. will need processing anyway
	try:
	  if soup.p.text.__len__() < 500 or soup.p.text.endswith(':'):
	    all_p = soup.find_all('p')
	    wt = ""
	    for idx, val in enumerate(all_p):
	      wt = (wt+"PARABREAK_REDDITQUOTE"+all_p[idx].text)
	    data = wt                                      # Post all paragraphs
	  else:
	    data = soup.p.text                             #Post only first paragraph
	except:
	  fail("BAD DATA FETCHED")
	  if what_is_call or tell_me_call:
	    try:
	      tell_me_text = wikipedia.summary(term,auto_suggest=False,redirect=True)
	      tell_me_link = wikipedia.page(term,auto_suggest=False).url
	      title = wikipedia.page(term,auto_suggest=False).title
	      if bool(re.search(title,tell_me_text)):
		summary = re.sub(title,"[**"+title+"**]("+tell_me_link+")",tell_me_text)
	      else:
		summary = "[**"+title+"**](" + tell_me_link + "): " + tell_me_text 
	      log("INTERPRETATION: %s"%filter(lambda x: x in string.printable, title))
	      if re.search(r'#',title):
		summary = wikipedia.page(title.split('#')[0]).section(title.split('#')[1])
		if summary == None or str(filter(lambda x: x in string.printable, summary)).strip() == "":
		  summary = "Sorry, I failed to fetch the section, but here's the link: "+wikipedia.page(title.split('#')[0]).url+"#"+title.split('#')[1]
	      comment = "*Here you go:*\n\n---\n\n>\n"+summary+"\n\n---\n\n[^(about)](http://www.reddit.com/r/autowikibot/wiki/index) ^| *^(/u/"+post.author.name+" can reply with 'delete'. Will also delete if comment's score is -1 or less.)*  ^| [^(**call me**: wikibot, what is something?)](http://www.reddit.com/r/autowikibot/wiki/commandlist)"
	      try:
		post.reply(comment)
		totalposted = totalposted + 1
		success("#%s REPLY SUCCESSFUL"%totalposted)
	      except Exception as e:
		warn("REPLY FAILED: %s @ %s"%(e,post.subreddit))# TODO add to badsubs on 403
	      continue
	    except Exception as e:### TODO this code might not be required. Review.
	      if bool(re.search('.*may refer to:.*',str(e))):
		comment = "*Can you be a little specific, please?*\n\n---\n\n>\n"+str(e).replace('\n','\n\n>')+"\n\n---\n\n[^(about)](http://www.reddit.com/r/autowikibot/wiki/index) ^| *^(/u/"+post.author.name+" can reply with 'delete'. Will also delete if comment's score is -1 or less.)*  ^| [^(**call me**: wikibot, what is something?)](http://www.reddit.com/r/autowikibot/wiki/commandlist)"
		log("ASKING FOR DISAMBIGUATION")
	      else:
		log("INTERPRETATION FAIL: %s"%term)
		try:
		  suggest = wikipedia.search(term,results=1)[0]
		  comment = "*You mean,* **"+suggest+"**?\n\n---\n\n[^(about)](http://www.reddit.com/r/autowikibot/wiki/index) ^| *^(/u/"+post.author.name+" can reply with 'delete'. Will also delete if comment's score is -1 or less.)*  ^| [^(**call me**: wikibot, what is something?)](http://www.reddit.com/r/autowikibot/wiki/commandlist)"
		  log("SUGGESTING %s"%suggest)
		except:
		  comment = "*" + term + "? Sorry, couldn't find that.\n\n---\n\n[^(about)](http://www.reddit.com/r/autowikibot/wiki/index) ^| *^(/u/"+post.author.name+" can reply with 'delete'. Will also delete if comment's score is -1 or less.)*  ^| [^(**call me**: wikibot, what is something?)](http://www.reddit.com/r/autowikibot/wiki/commandlist)"
		  log("COULD NOT SUGGEST FOR %s",term)
		try:
		  post.reply(comment)
		  totalposted = totalposted + 1
		  success("#%s REPLY SUCCESSFUL"%totalposted)
		except Exception as e:
		  warn("REPLY FAILED: %s @ %s"%(e,post.subreddit))# TODO add to badsubs on 403
		continue
	  continue
	data = strip_wiki(data)
	
	data = re.sub("Cite error: There are ref tags on this page, but the references will not show without a \{\{reflist\}\} template \(see the help page\)\.", '', data)
	
	### Add quotes for markdown
	data = re.sub(r"PARABREAK_REDDITQUOTE", '\n\n>', data)
	
	if data.__len__() > 1500:
	  log("TEXT CUT AT 1500 CHARACTERS")
	  data = split_by_length(data,1500)[0]+" ... \n`(Introduction too large, cut at 1500 characters)`"
	
	if data.__len__() < 50:
	  continue
	success("TEXT PACKAGED")
	
	### Fetch page image from wikipedia
	try:
	  ### Extract image url
	  try:
	    image_name = ppsoup.pageprops["page_image"]
	    image_name = image_name.decode('utf-8','ignore')
	  except:
	    raise Exception("NO PAGE IMAGE")
	  if image_name.endswith("svg") or image_name.endswith("ogg"):
	    raise Exception("IMAGE TYPE UNSUPPORTED BY IMGUR")
	  url = ("http://en.wikipedia.org/w/api.php?action=query&titles=File:"+image_name+"&prop=imageinfo&iiprop=url|mediatype&iiurlwidth=640&format=xml")
	  wi_api_data = urllib2.urlopen(url).read()
	  wisoup = BeautifulSoup(wi_api_data)
	  image_url = wisoup.ii['thumburl']
	  image_source_url = wisoup.ii['descriptionurl']
	  image_source_url = re.sub(r'\)','\)',image_source_url)
	  image_source_url = re.sub(r'\(','\(',image_source_url)
	  global image_source_markdown
	  image_source_markdown = ("[^(image source)]("+image_source_url+") ^| ")
	  
	  ### Upload to imgur
	  uploaded_image = im.upload_image(url=image_url, title=image_name)
	  
	  ### Extract caption from already fetched sectiondata
	  try:
	    if globalsoup.find("div", { "class" : "thumbcaption" }):
	      caption_div = globalsoup.find("div", { "class" : "thumbcaption" })
	    else:
	      raise Exception("CAPTION NOT PACKAGED: IMAGE HAS NO CAPTION")
	    if image_name not in str(caption_div.find("div", { "class" : "magnify" })):
	      raise Exception("CAPTION NOT PACKAGED: IMAGE IS NOT PAGE'S MAIN IMAGE")
	    discard = caption_div.find("div", { "class" : "magnify" }).extract()
	    caption = caption_div.text.strip()
	    caption = strip_wiki(caption)
	    caption = re.sub(r'\)','\)',caption)
	    caption = re.sub(r'\(','\(',caption)
	    caption = re.sub(r'\*','',caption)
	    caption = re.sub(r'\n',' ',caption)
	    caption = re.sub(r' ',' ^',caption)
	    if caption != "":
	      caption_markdown = (" ^- **^"+caption+"**")
	      success("CAPTION PACKAGED")
	  except Exception as e:
	    caption_markdown = ""
	    log(e)
	  image_markdown = ("\n\n[^(**Picture**)]("+uploaded_image.link+")"+caption_markdown)
	  success("IMAGE PACKAGED VIA %s"%uploaded_image.link)
	except Exception as e:
	  image_markdown = ""
	  image_source_markdown = ""
	  log("IMAGE: %s"%str(e).strip().replace('\n',''))
	
	post_markdown = ("*"+bit_comment_start+"Wikipedia article about* [***"+article_name_terminal+"***](http://en.wikipedia.org/wiki/"+url_string+") : \n\n---\n\n>"+data+"\n\n---"+image_markdown+"\n\n"+image_source_markdown+"[^(about)](http://www.reddit.com/r/autowikibot/wiki/index) ^| *^(/u/"+post.author.name+" can reply with 'delete'. Will also delete if comment's score is -1 or less.)*  ^| [^(**call me**: wikibot, what is something?)](http://www.reddit.com/r/autowikibot/comments/1ux484/ask_wikibot/) ^| [^(flag for glitch)](http://www.reddit.com/message/compose?to=acini&subject=bot%20glitch&message=%0Acontext:"+post.permalink+")")
	### post
	try:
	  post.reply (post_markdown)
	  totalposted = totalposted + 1
	  success("#%s LINK REPLY SUCCESSFUL"%totalposted)
	except Exception as e:
	  warn("REPLY FAILED: %s @ %s"%(e,sub))# TODO add to badsubs on 403
	  continue
	recieved_banned_users = list(shared.get('banned_users')) #TODO communicate badsubs
	banned_users = recieved_banned_users+banned_users
	banned_users = list(set(banned_users))
  except KeyboardInterrupt:
    save_changing_variables()
    warn("EXITING")
    break
  except Exception as e: 
    traceback.print_exc()
    warn("GLOBAL: %s"%e)
    time.sleep(3)
    continue
  