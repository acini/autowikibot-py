# -*- coding: utf-8 -*-

import praw, time, datetime, re, urllib, urllib2, pickle, pyimgur, os, traceback, wikipedia, string, socket
from util import success, warn, log, fail, special, bluelog
from bs4 import BeautifulSoup
from HTMLParser import HTMLParser

### Uncomment to debug
#import logging
#logging.basicConfig(level=logging.DEBUG)

### Set root directory to script directory
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

###Load data
def load_data():
  global banned_users
  global badsubs
  global totalposted
  global imgur_client_id
  global banned_users_comment
  global badsubs_comment
  global totalposted_comment
  imgur_client_id = datafile_lines[2].strip()
  banned_users_comment = "t1_"+datafile_lines[3].strip()
  badsubs_comment = "t1_"+datafile_lines[4].strip()
  totalposted_comment = "t1_"+datafile_lines[5].strip()
  try:
    banned_users = r.get_info(thing_id=banned_users_comment).body.split()
    badsubs = r.get_info(thing_id=badsubs_comment).body.split()
    totalposted = int(float(r.get_info(thing_id=totalposted_comment).body))
    success("DATA LOADED")
  except Exception as e:
    traceback.print_exc()
    fail("DATA LOAD FAILED: %s"%e)
    exit()

def save_changing_variables():
  badsubs.sort()
  c_badsubs = ""
  for item in badsubs:
    c_badsubs = item+"\n"+c_badsubs
  c_badsubs.strip()
  r.get_info(thing_id=badsubs_comment).edit(c_badsubs)
  time.sleep(1)
  
  r.get_info(thing_id=totalposted_comment).edit(totalposted)
  time.sleep(1)

  success("DATA SAVED")

with open ('datafile.inf', 'r') as myfile:
  datafile_lines=myfile.readlines()

### Login
r = praw.Reddit("autowikibot by /u/acini at /r/autowikibot")
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
	  fail("%s"%e)
	  time.sleep(5)
    

def post_reply(reply,post):
  global totalposted
  try:
    reply = "#####&#009;\n\n######&#009;\n\n####&#009;\n"+reply
    post.reply(reply)
    totalposted = totalposted + 1
    success("#%s REPLY SUCCESSFUL"%totalposted)
    return True
  except Exception as e:
    warn("REPLY FAILED: %s @ %s"%(e,post.subreddit))
    if str(e) == '403 Client Error: Forbidden':
      badsubs = r.get_info(thing_id=badsubs_comment).body.split()
      badsubs.append(str(post.subreddit))
      save_changing_variables()
    return False
	    
def filterpass(post):
  global summary_call
  global has_link
  if (post.author.name == USERNAME) or post.author.name in banned_users:
    return False
  summary_call = re.search("wikibot.*?wh.*?(\'s|is a |is an|is|are|was)",post.body.lower()) or re.search("wikibot.*?tell .*? about",post.body.lower()) or re.search("\?\-.*\-\?",post.body.lower())
  has_link = any(string in post.body for string in ['://en.wikipedia.org/wiki/', '://en.m.wikipedia.org/wiki/'])
  if has_link or summary_call:
    if re.search(r"&gt;", post.body) and not summary_call:
      return False
    elif re.search(r"wikipedia.org/wiki/.*wikipedia.org/wiki/", post.body, re.DOTALL):
      return False
    elif str(post.subreddit) in badsubs:
      return False
    elif any(string in post.body for string in ['/wiki/File:', '/wiki/List_of', '/wiki/User:', '/wiki/Template:', '/wiki/Category:', '/wiki/Wikipedia:']):
      return False
    else:
      return True

def get_url_string(post):
  try:
    after_split = post.body.split("wikipedia.org/wiki/")[1]
    for e in ['\n', ' ']:
      after_split = after_split.split(e)[0]
    if after_split.endswith(')') and not re.search(r'\(',after_split):
      after_split = after_split.split(')')[0]
    if re.search(r'\)',after_split) and not re.search(r'\(',after_split):
      after_split = after_split.split(')')[0]
    return after_split
  except:
    pass
   
def process_summary_call(post):
  special("__________________________________________________")
  special("SUMMARY CALL: %s"%post.id)
  if re.search('wikibot.*?tell .*? about ',post.body.lower()) or re.search("wikibot.*?wh.*?(\'s|is a |is an|is|are|was)",post.body.lower()):
    if re.search('wikibot.*?tell .*? about ',post.body.lower()):
      post_body = re.sub('wikibot.*?tell .*? about ','__BODYSPLIT__',post.body.lower())
    else:
      post_body = re.sub('wikibot.*?wh.*?(\'s|is a |is an|is|are|was) ','__BODYSPLIT__',post.body.lower())
    term = post_body.split('__BODYSPLIT__')[1]
    term = re.sub('\?','\n',term)
    if term[0:2] == 'a ':
      term = term[2:term.__len__()]
    if term[0:4] == 'the ':
      term = term[4:term.__len__()]
    if term.endswith('.'):
      term = term[0:--(term.__len__()-1)]
    try:
      term = term.split('\n')[0]
    except:
      log("COULD NOT SPLIT")
      pass
  elif re.search("\?\-.*\-\?",post.body.lower()):
    term = re.search("\?\-.*\-\?",post.body.lower()).group(0).strip('$').strip('-').strip()
    
  log("TERM: %s"%filter(lambda x: x in string.printable, term))
  if term.lower().strip() == 'love':
    post_reply('*Baby don\'t hurt me! Now seriously, stop asking me about love so many times! O.o What were we discussing about in this thread again?*',post)
    return(False,False)
  if term.lower().strip() == 'wikibot':
    post_reply('*Me! I know me.*',post)
    return(False,False)
  if term.lower().strip() == 'reddit':
    post_reply('*This place. It feels like home.*',post)
    return(False,False)
  if term.strip().__len__() < 2 or term == None:
    log("EMPTY TERM")
    return(False,False)
  try:
    title = wikipedia.page(term,auto_suggest=False).title
    if title.lower() == term:
      bit_comment_start = ""
    elif title.lower() != term:
      try:
	discard = wikipedia.page(term,auto_suggest=False,redirect=False).title
      except Exception as e:
	if re.search('resulted in a redirect',str(e)):
	  bit_comment_start = "*\"" + term.strip() + "\" redirects to* "
    else:
      bit_comment_start = "*Couldn't find Wikipedia article titled \"" + term.strip() + "\". Closest match is* "
    if re.search(r'#',title):
      url = wikipedia.page(title.split('#')[0],auto_suggest=False).url
      sectionurl =  url + "#" + title.split('#')[1]
      comment = "*Couldn't find Wikipedia article titled \"" + term.strip() + "\". But I found a relevant section ["+title.split('#')[1]+"]("+sectionurl.replace(')','\)')+") in article ["+title.split('#')[0]+"]("+url+") that might interest you.*\n\n---\n\n[^(about)](http://www.reddit.com/r/autowikibot/wiki/index) ^| *^(/u/"+post.author.name+" can reply with 'delete'. Will also delete if comment's score is -1 or less.)*  ^| ^(**Summon**: wikibot, what is something?)"
      post_reply(comment,post)
      log("RELEVANT SECTION SUGGESTED: %s"%filter(lambda x: x in string.printable, title))
      return (False,False)
    url_string = title
    log("INTERPRETATION: %s"%filter(lambda x: x in string.printable, title))
    return (url_string,bit_comment_start)
  except Exception as e:
    if bool(re.search('.*may refer to:.*',filter(lambda x: x in string.printable, str(e)))):
      deflist = "\n\nI found 3 most common meanings for you:\n\n"
      for idx, val in enumerate(filter(lambda x: x in string.printable, str(e)).split('may refer to: \n')[1].split('\n')):
	deflist = deflist + "\n\n>* " + wikipedia.summary(val,auto_suggest=True,sentences=1)
	if idx > 1:
	  break
      summary = "*Oh, there's too many of \""+term.strip()+"\".*\n\n---"+deflist+"\n\n---\n\nOtherwise, "+str(e).replace('\n','\n\n>')+"\n\n---\n\n[^(about)](http://www.reddit.com/r/autowikibot/wiki/index) ^| *^(/u/"+post.author.name+" can reply with 'delete'. Will also delete if comment's score is -1 or less.)*  ^| ^(**Summon**: wikibot, what is something?)"
      log("ASKING FOR DISAMBIGUATION")
    else:
      log("INTERPRETATION FAIL: %s"%filter(lambda x: x in string.printable, term))
      try:
	terms = "\""+term+"\""
	suggesttitle = str(wikipedia.search(terms,results=1)[0])
	log("SUGGESTING: %s"%filter(lambda x: x in string.printable, suggesttitle))
	if suggesttitle.lower() == term:
	  bit_comment_start = ""
	else:
	  bit_comment_start = "*Couldn't find Wikipedia article titled \"" + term.strip() + "\". Here\'s the closest match:*"
	if str(suggesttitle).endswith(')') and not re.search('\(',str(suggesttitle)):
	  suggesttitle = suggesttitle[0:--(suggesttitle.__len__()-1)]
	return (str(suggesttitle),bit_comment_start)
      except:
	trialtitle = wikipedia.page(term,auto_suggest=True).title
	if trialtitle.lower() == term:
	  bit_comment_start = ""
	else:
	  bit_comment_start = "*Couldn't find Wikipedia article titled \"" + term.strip() + "\". By long shot, here's the closest match:*"
	log("TRIAL SUGGESTION: %s"%filter(lambda x: x in string.printable, trialtitle))  
	if str(trialtitle).endswith(')') and not re.search('\(',str(trialtitle)):
	  trialtitle = trialtitle[0:--(trialtitle.__len__()-1)]
	return (str(trialtitle),bit_comment_start)
    post_reply(summary,post)
    return (False,False)

def clean_soup(soup):
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
  return soup

def reddify(html):
  html = html.replace('&lt;b&gt;', '**')
  html = html.replace('&lt;/b&gt;', '**')
  html = re.sub('&lt;sup&gt;','^',html)
  html = re.sub('&lt;sup.*?&gt;','',html)
  html = html.replace('&lt;/sup&gt;','')
  return html

def strip_wiki(wiki):
  wiki = re.sub('\[[0-9]\]','',wiki)
  wiki = re.sub('\[[0-9][0-9]\]','',wiki)
  wiki = re.sub('\[[0-9][0-9][0-9]\]','',wiki)
  wiki = re.sub("\( listen\)", '', wiki)
  return wiki

def truncate(data, length):
  if data.__len__() > length:
    log("TEXT CUT AT %s CHARACTERS"%length)
    data = data[0:length]+" ... \n`(Truncated at "+str(length)+" characters)`"
    return data
  else:
    return data
  
def process_brackets_links(string):
  string = ("%s)"%string)
  string = string.replace("\\", "")
  return string

def process_brackets_syntax(string):
  string = string.replace("\\", "")
  string = ("%s\)"%string)
  return string
  
### declare variables
load_data()
im = pyimgur.Imgur(imgur_client_id)
global pagepropsdata
lastload = int(float(time.strftime("%s")))

while True:
  try:
    #comments = r.get_comments("all",limit = 1000)
    #for post in comments:
    for post in praw.helpers.comment_stream(r,'all', limit = None):
      
      ### Dirty timer hack
      now = int(float(time.strftime("%s")))
      diff = now - lastload
      if diff > 899:
	banned_users = r.get_info(thing_id=banned_users_comment).body.split()
	success("BANNED USER LIST RENEWED")
	save_changing_variables()
	lastload = now
      
      
      if filterpass(post):
	if has_link:
	  url_string = get_url_string(post)
	  log("__________________________________________________")
	  log("LINK TRIGGER: %s"%post.id)
	  bit_comment_start = "*Here's a bit from linked Wikipedia article about*"
	else:
	  try:
	    url_string = ""
	    url_string, bit_comment_start = process_summary_call(post)
	    if url_string == False:
	      continue
	    url_string = str(url_string)
	  except Exception as e:
	    if bool(re.search('.*may refer to:.*',filter(lambda x: x in string.printable, str(e)))):
	      deflist = "\n\nI found 3 most common meanings for you:\n\n"
	      for idx, val in enumerate(filter(lambda x: x in string.printable, str(e)).split('may refer to: \n')[1].split('\n')):
		deflist = deflist + "\n\n>* " + wikipedia.summary(val,auto_suggest=True,sentences=1)
		if idx > 1:
		  break
	      summary = "*Oh, there's too many of \""+url_string.strip()+"\".*\n\n---"+deflist+"\n\n---\n\nOtherwise, "+str(e).replace('\n','\n\n>')+"\n\n---\n\n[^(about)](http://www.reddit.com/r/autowikibot/wiki/index) ^| *^(/u/"+post.author.name+" can reply with 'delete'. Will also delete if comment's score is -1 or less.)*  ^| ^(**Summon**: wikibot, what is something?)"
	      log("ASKING FOR DISAMBIGUATION")
	      post_reply(summary,post)
	      continue
	  if not url_string:
	    continue
	if url_string.endswith('))'):
	  url_string = url_string.replace('))',')')
	url_string_for_fetch = url_string.replace('_', '%20').replace("\\", "")
	url_string_for_fetch = url_string_for_fetch.replace(' ', '%20').replace("\\", "")
	article_name = url_string.replace('_', ' ')
	
	### In case user comments like "/wiki/Article.", remove last 1 letter
	if url_string_for_fetch.endswith(".") or url_string_for_fetch.endswith("]"):
	  url_string_for_fetch = url_string_for_fetch[0:--(url_string_for_fetch.__len__()-1)]
	
	### check for subheading in url string, process if present
	if re.search(r"#",article_name) and not summary_call:
	  pagename = article_name.split('#')[0]
	  if re.search('List of',pagename):
	      log('IS A LIST')
	      continue
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
	    page = wikipedia.page(pagename.encode('utf-8','ignore'),auto_suggest=False)
	    section = page.section(sectionname.encode('utf-8','ignore'))
	    if section == None or str(section.encode('utf-8','ignore')).strip() == "":
	      raise Exception("SECTION RETURNED EMPTY")
	    sectionname = sectionname.replace('_',' ')
	    link = page.url+"#"+sectionname
	    link = link.replace(')','\)')
	    page_url = page.url.replace(')','\)')
	    section = section.replace('\n','\n\n>')
	    success("TEXT PACKAGED")
	    section = truncate(section,1500)
	    comment = ("*Here's the linked section ["+sectionname+"]("+link+") from Wikipedia article ["+page.title+"]("+page_url+")* : \n\n---\n\n>"+section+"\n\n---\n\n[^(about)](http://www.reddit.com/r/autowikibot/wiki/index) ^| *^(/u/"+post.author.name+" can reply with 'delete'. Will also delete if comment's score is -1 or less.)*  ^| ^(**Summon**: wikibot, what is something?)")
	    post_reply(comment,post)
	  except Exception as e:
	    #traceback.print_exc()
	    warn("SECTION PROCESSING: %s"%e)
	    continue
	  continue
	
	
	
	### fetch data from wikipedia
	
	url = ("http://en.wikipedia.org/w/api.php?action=query&titles="+url_string_for_fetch+"&prop=pageprops&format=xml")
	try:
	  socket.setdefaulttimeout(30)
	  pagepropsdata = urllib2.urlopen(url).read()
	  pagepropsdata = pagepropsdata.decode('utf-8','ignore')
	  ppsoup = BeautifulSoup(pagepropsdata)
	  article_name_terminal = ppsoup.page['title']
	except:
	  try:
	    article_name_terminal = article_name.replace('\\', '')
	  except:
	    article_name_terminal = article_name.replace('\\', '').decode('utf-8','ignore')
	
	log("TOPIC: %s"%filter(lambda x: x in string.printable, article_name_terminal))
	url = ("http://en.wikipedia.org/w/api.php?action=parse&page="+url_string_for_fetch+"&format=xml&prop=text&section=0&redirects")
	try:
	  socket.setdefaulttimeout(30)
	  sectiondata = urllib2.urlopen(url).read()
	  sectiondata = sectiondata.decode('utf-8','ignore')
	  sectiondata = reddify(sectiondata)
	  soup = BeautifulSoup(sectiondata)
	  soup = BeautifulSoup(soup.text)
	  section0soup = soup
	except Exception as e:
	  fail("FETCH: %s"%e)
	  continue
	
	soup = clean_soup(soup)
	
	### extract paragraph
	try:
	  if soup.p.text.__len__() < 500:
	    all_p = soup.find_all('p')
	    wt = ""
	    for idx, val in enumerate(all_p):
	      wt = (wt+"\n\n>"+all_p[idx].text)
	    data = wt                                      # Post all paragraphs
	  else:
	    data = soup.p.text                             #Post only first paragraph
	except:
	  fail("BAD DATA FETCHED")
	  if summary_call:
	    try:
	      term = url_string
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
		  page_url = wikipedia.page(title.split('#')[0]).url
		  summary = "Sorry, I failed to fetch the section, but here's the link: "+page_url+"#"+title.split('#')[1]
	      if re.search(r'(',page_url):
		page_url = process_brackets_links(page_url)
	      comment = "*Here you go:*\n\n---\n\n>\n"+summary+"\n\n---\n\n[^(about)](http://www.reddit.com/r/autowikibot/wiki/index) ^| *^(/u/"+post.author.name+" can reply with 'delete'. Will also delete if comment's score is -1 or less.)*  ^| ^(**Summon**: wikibot, what is something?)"
	      post_reply(comment,post)
	      continue
	    except Exception as e:
	      if bool(re.search('.*may refer to:.*',filter(lambda x: x in string.printable, str(e)))):
		deflist = "\n\nI found 3 most common meanings for you:\n\n"
		for idx, val in enumerate(filter(lambda x: x in string.printable, str(e)).split('may refer to: \n')[1].split('\n')):
		  deflist = deflist + "\n\n>* " + wikipedia.summary(val,auto_suggest=True,sentences=1)
		  if idx > 1:
		    break
		comment = "*Oh, there's too many of \""+process_brackets_syntax(url_string).strip()+"\".*\n\n---"+deflist+"\n\n---\n\nOtherwise, "+str(e).replace('\n','\n\n>')+"\n\n---\n\n[^(about)](http://www.reddit.com/r/autowikibot/wiki/index) ^| *^(/u/"+post.author.name+" can reply with 'delete'. Will also delete if comment's score is -1 or less.)*  ^| ^(**Summon**: wikibot, what is something?)"
		log("ASKING FOR DISAMBIGUATION")
	      else:
		log("INTERPRETATION FAIL: %s"%term)
		try:
		  terms = "\""+term+"\""
		  suggest = wikipedia.search(terms,results=1)[0]
		  trialsummary = wikipedia.summary(suggest,auto_suggest=True)
		  comment = "*No Wikipedia article exists for \""+term.trim()+"\"* **"+suggest+"** is the closest match I could find.\n\n---\n\n>"+trialsummary+"\n\n---\n\n[^(about)](http://www.reddit.com/r/autowikibot/wiki/index) ^| *^(/u/"+post.author.name+" can reply with 'delete'. Will also delete if comment's score is -1 or less.)*  ^| ^(**Summon**: wikibot, what is something?)"
		  log("SUGGESTING %s"%suggest)
		except:
		  comment = "*Sorry, couldn't find a wikipedia article about that or I had processing error due to overload on Wikipedia servers.*\n\n---\n\n[^(about)](http://www.reddit.com/r/autowikibot/wiki/index) ^| *^(/u/"+post.author.name+" can reply with 'delete'. Will also delete if comment's score is -1 or less.)*  ^| ^(**Summon**: wikibot, what is something?)"
		  log("COULD NOT SUGGEST FOR %s"%term)
		post_reply(comment,post)
		continue
	  continue
	data = strip_wiki(data)
	data = re.sub("Cite error: There are ref tags on this page, but the references will not show without a \{\{reflist\}\} template \(see the help page\)\.", '', data)
	data = truncate(data,1000)
	if data.__len__() < 50:
	  log("TOO SMALL INTRODUCTION PARAGRAPH")
	  continue
	success("TEXT PACKAGED")
	
	### Fetch page image from wikipedia
	try:
	  ### Extract image url
	  try:
	    page_image = ppsoup.pageprops["page_image"]
	    page_image = urllib.unquote(page_image.decode('utf-8','ignore'))
	  except:
	    raise Exception("NO PAGE IMAGE")
	  if page_image.endswith("ogg"):
	    raise Exception("BAD IMAGE")
	  url = ("http://en.wikipedia.org/w/api.php?action=query&titles=File:"+page_image+"&prop=imageinfo&iiprop=url|mediatype&iiurlwidth=640&format=xml")
	  socket.setdefaulttimeout(30)
	  wi_api_data = urllib2.urlopen(url).read()
	  wisoup = BeautifulSoup(wi_api_data)
	  image_url = wisoup.ii['thumburl']
	  image_source_url = wisoup.ii['descriptionurl']
	  image_source_url = re.sub(r'\)','\)',image_source_url)
	  image_source_url = re.sub(r'\(','\(',image_source_url)
	  global image_source_markdown
	  image_source_markdown = ("[^(image source)]("+image_source_url+") ^| ")
	  
	  ### Upload to imgur
	  uploaded_image = im.upload_image(url=image_url, title=page_image)
	  
	  ### Extract caption from already fetched sectiondata
	  try:
	    caption_div = section0soup.find("div", { "class" : "thumbcaption" })
	    pic_markdown = "Picture"
	    if caption_div is None:
	      raise Exception("CAPTION NOT PACKAGED: NO CAPTION FOUND IN SECTION 0")
	    if page_image not in str(caption_div.find("div", { "class" : "magnify" })):
	      raise Exception("CAPTION NOT PACKAGED: PAGE IMAGE NOT IN SECTION 0")
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
	      caption_div = None
	      success("CAPTION PACKAGED")
	    else:
	      raise Exception("CAPTION NOT PACKAGED: NO CAPTION FOUND IN SECTION 0")
	  except Exception as e:
	    if str(e) == "CAPTION NOT PACKAGED: PAGE IMAGE HAS NO CAPTION":
	      pic_markdown = "Picture"
	    elif str(e) == "CAPTION NOT PACKAGED: PAGE IMAGE NOT IN SECTION 0":
	      pic_markdown = "Related Picture"
	    caption_markdown = ""
	    log(e)
	  image_markdown = ("[^(**"+pic_markdown+"**)]("+uploaded_image.link+")"+caption_markdown)
	  success("IMAGE PACKAGED VIA %s"%uploaded_image.link)
	except Exception as e:
	  image_markdown = ""
	  image_source_markdown = ""
	  #traceback.print_exc()
	  log("IMAGE: %s"%str(e).strip().replace('\n',''))
	  
	###Interesting articles
	try:
	  intlist = wikipedia.search(article_name_terminal,results=5)
	  if intlist.__len__() > 1:
	    if article_name_terminal in intlist:
	      intlist.remove(article_name_terminal)
	    interesting_list = ""
	    for topic in intlist:
	      try:
		topicurl = wikipedia.page(topic).url.replace('(','\(').replace(')','\)')
	      except:
		continue
	      topic = topic.replace(' ',' ^').replace(' ^(',' ^\(')
	      interesting_list = interesting_list + " [^" + topic + "]" + "(" +topicurl+ ") ^|"
	    interesting_markdown = "^Interesting:"+interesting_list.strip('^|')
	    success("%s INTERESTING ARTICLE LINKS PACKAGED"%intlist.__len__())
	  else:
	    raise Exception("NO SUGGESTIONS")
	except Exception as e:
	  interesting_markdown = ""
	  traceback.print_exc()
	  log("INTERESTING ARTICLE LINKS NOT PACKAGED: %s"%str(e).strip().replace('\n',''))
	
	post_markdown = (bit_comment_start+" [***"+article_name_terminal+"***](http://en.wikipedia.org/wiki/"+url_string_for_fetch.replace(')','\)')+") : \n\n---\n\n>"+data+"\n\n>"+image_markdown+"\n\n---\n\n"+interesting_markdown+"\n\n"+image_source_markdown+"[^(about)](http://www.reddit.com/r/autowikibot/wiki/index) ^| *^(/u/"+post.author.name+" can reply with 'delete'. Will delete if comment's score is -1 or less.)*  ^| ^(**Summon**: wikibot, what is something?) ^| [^(flag for glitch)](http://www.reddit.com/message/compose?to=/r/autowikibot&subject=bot%20glitch&message=%0Acontext:"+post.permalink+")")
	a = post_reply(post_markdown,post)
	if not a:
	  continue
	
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
  
