# -*- coding: utf-8 -*-
import praw, time, datetime, re, urllib, urllib2, pickle, pyimgur, os, traceback, memcache
from util import success, warn, log, fail
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
  #html = html.replace('<i>', '*')
  #html = html.replace('</i>', '*')
  return html

def strip_wiki(wiki):
  wiki = re.sub("\[.*?\]", '', wiki)
  wiki = re.sub("\( listen\)", '', wiki)
  return wiki

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
    log("Loading")
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
    success("Data loaded")
  except:
    file_warning()
    exit()

def save_changing_variables():
  with open('banned_users', 'w+') as myfile:
    for item in banned_users:
      myfile.write("%s\n" % item)
  with open('badsubs', 'w+') as myfile:
    for item in badsubs:
      myfile.write("%s\n" % item)
  with open('already_done_dump', 'w+') as myfile:
    for item in already_done:
      myfile.write("%s\n" % item)
  with open('totalposted', 'w') as f:#TODO replace pickle with simple write
    pickle.dump(totalposted, f)
  success("Data saved")

  
### declare variables
load_data()
r = praw.Reddit("autowikibot by /u/acini at /r/autowikibot")
im = pyimgur.Imgur(imgur_client_id)
linkWords = ['://en.wikipedia.org/wiki/', '://en.m.wikipedia.org/wiki/']
endoflinkWords = ['\n', ' ', '/']
pagepropsdata = ""
  
### Login
USERNAME = userpass_lines[0].strip()
PASSWORD = userpass_lines[1].strip()

Trying = True
while Trying:
        try:
                r.login(USERNAME, PASSWORD)
		success("Logged in.")
                Trying = False
        except praw.errors.InvalidUserPass:
                fail("Wrong username or password.")
                exit()
        except Exception as e:
	  fail("%s"%e)
	  time.sleep(5)
	
while True:
  try:
    #comments = r.get_comments("all",limit = 1000)
    #for post in comments:
    for post in praw.helpers.comment_stream(r,'all', limit = None):
      
      ### check if comment has links quotes or is previously processed
      has_link = any(string in post.body for string in linkWords)
      if has_link:
	### check if comment is already processed, skip if it is
	if post.id in already_done:
	  #warn("Previously processed")
	  continue
	### check comment body quotes, skip if present
	if re.search(r"&gt;", post.body):
	  already_done.append(post.id)
	  #warn("Has quote")
	  continue
	### check comment body for more than one wikipedia link, skip if present
	if re.search(r"wikipedia.org/wiki/.*wikipedia.org/wiki/", post.body, re.DOTALL):
	  already_done.append(post.id)
	  #warn("Has second link") #TODO process 2nd link
	  continue
	### check if comment is bot's own post, skip if it is
	if (post.author.name == USERNAME):
	  already_done.append(post.id)
	  #warn("My comment")
	  continue
	if post.author.name in banned_users:
	  already_done.append(post.id)
	  #warn("Banned user")
	  continue
	
	### Proceed with processing as minumum criteria are satisfied.
	already_done.append(post.id)
	
	### check if comment is from excluded subreddit, skip if it is
	link = post.permalink
	link = link.split("http://www.reddit.com/r/")[1]
	sub = link.split("/")[0]
	sublower = sub.lower()
	if str(sublower) in badsubs:
	  #warn("Excluded sub")
	  continue
	
	### process url string
	after_split = post.body.split("wikipedia.org/wiki/")[1]
	
	### Seprate url string from mistakenly put characters in front of it (commenter mistake)
	if re.search(r'\)#',after_split):
	  for e in endoflinkWords:
	    after_split = after_split.split(e)[0]
	else:
	  for e in endoflinkWords:
	    after_split = after_split.split(e)[0]
	  after_split = after_split.split(")")[0]
	
	url_string = after_split
	url_string_for_fetch = url_string.replace('_', '%20')
	article_name = url_string.replace('_', ' ')
	
	### url string correction for brackets
	if re.search(r"[(]", url_string_for_fetch):
	  url_string_for_fetch = ("%s)"%url_string_for_fetch)
	  url_string_for_fetch = url_string_for_fetch.replace("\\", "")
	  article_name = ("%s)"%article_name)
	  url_string = url_string.replace("\\", "")
	  url_string = ("%s\)"%url_string)
	
	
	### In case user comments like "/wiki/Article.", remove last 1 letter
	if url_string_for_fetch.endswith(".") or url_string_for_fetch.endswith("]"):
	  url_string_for_fetch = url_string_for_fetch[0:--(url_string_for_fetch.__len__()-1)]
	
	log(post.id)
	
	### check for subheading in url string, skip if present #TODO process subheading requests
	if re.search(r"#",article_name):
	  warn("Links to subheading")
	  continue
	
	### check if link is wikipedia namespace, skip if present
	has_hash = re.search(r":",article_name) and not re.search(r": ",article_name)
	if has_hash:
	  warn("Namespace link")
	  continue

	### check if article is a list, skip if it is
	if re.search(r"List of.*",article_name):
	  #warn("Is a list")
	  continue
	
	### fetch data from wikipedia
	
	url = ("http://en.wikipedia.org/w/api.php?action=query&titles="+url_string_for_fetch+"&prop=pageprops&format=xml")
	try:
	  pagepropsdata = urllib2.urlopen(url).read()
	  pagepropsdata = pagepropsdata.decode('utf-8')
	  ppsoup = BeautifulSoup(pagepropsdata)
	  article_name_terminal = ppsoup.page['title']
	except:
	  article_name_terminal = article_name.replace('\\', '').decode('utf-8')
	
	log(article_name_terminal.encode('utf-8'))
	url = ("http://en.wikipedia.org/w/api.php?action=parse&page="+url_string_for_fetch+"&format=txt&prop=text&section=0&redirects")
	try:
	  sectiondata = urllib2.urlopen(url).read()
	  sectiondata = sectiondata.decode('utf-8')
	  sectiondata = reddify(sectiondata)
	  soup = BeautifulSoup(sectiondata)
	  globalsoup = soup
	except Exception as e:
	  fail("Fetch: %s"%e)
	  continue
	
	

	### Delete any tables, remove coordinates, cite error
	while soup.table:
	  discard = soup.table.extract()
	while soup.find(id='coordinates'):
	  discard = soup.find(id='coordinates').extract()
	while soup.find("strong", { "class" : "error mw-ext-cite-error" }):
	  discard = soup.find("strong", { "class" : "error mw-ext-cite-error" }).extract()
	while soup.find("span", { "class" : "t_nihongo_help noprint" }):
	  discard = soup.find("span", { "class" : "t_nihongo_help noprint" }).extract()
	
	### extract paragraph
	### <!-- is used as ending because it is present with every api fetch
	### Replace <!-- with </p> to get only first paragraph instead of full introduction
	### Not using xml parsing because tables etc. will need processing anyway
	try:
	  if soup.p.text.__len__() < 300 or soup.p.text.endswith(':'):
	    all_p = soup.find_all('p')
	    wt = ""
	    for idx, val in enumerate(all_p):
	      wt = (wt+"PARABREAK_REDDITQUOTE"+all_p[idx].text)
	    data = wt                                      # Post all paragraphs
	  else:
	    data = soup.p.text                             #Post only first paragraph
	except:
	  fail("Bad data fetched")
	  continue
	data = strip_wiki(data)
	
	data = re.sub("Cite error: There are ref tags on this page, but the references will not show without a \{\{reflist\}\} template \(see the help page\)\.", '', data)
	
	### Fetch page image from wikipedia
	try:
	  ### Extract image url
	  try:
	    image_name = ppsoup.pageprops["page_image"]
	  except:
	    raise Exception("none on page")
	  if image_name.endswith("svg") or image_name.endswith("ogg"):
	    raise Exception("Image type unsupported by imgur")
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
	    caption_div = globalsoup.find("div", { "class" : "thumbcaption" })
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
	  except:
	    caption_markdown = ""
	    #warn("No caption")
	  image_markdown = ("\n\n[^(**Picture**)]("+uploaded_image.link+")"+caption_markdown)
	  log(uploaded_image.link)
	except Exception as e:
	  image_markdown = ""
	  image_source_markdown = ""
	  #warn("No image: (%s)"%e)
	
	### Add quotes for markdown
	data = re.sub(r"PARABREAK_REDDITQUOTE", '\n\n>', data)
	
	post_markdown = ("*A bit from linked Wikipedia article about* [***"+article_name_terminal+"***](http://en.wikipedia.org/wiki/"+url_string+") : \n\n---\n\n>"+data+"\n\n---"+image_markdown+"\n\n"+image_source_markdown+"[^(about)](http://www.reddit.com/r/autowikibot/wiki/index) ^| *^(/u/"+post.author.name+" can reply with 'delete' if required. Also deletes if comment's score is -1 or less.)*  ^| [^(commands)](http://www.reddit.com/r/autowikibot/wiki/commandlist) ^| [^(flag for glitch)](http://www.reddit.com/message/compose?to=acini&subject=bot%20glitch&message=%0Acontext:"+post.permalink+")")
	### post
	try:
	  post.reply (post_markdown)
	  totalposted = totalposted + 1
	  success("(#%s) %s"%(totalposted,post.permalink))
	except Exception as e:
	  fail("Post Reply: %s @ %s"%(e,sub))
	  continue
	recieved_banned_users = list(shared.get('banned_users')) #TODO communicate badsubs
	banned_users = recieved_banned_users+banned_users
	banned_users = list(set(banned_users))
  except KeyboardInterrupt:
    save_changing_variables()
    log("Bye!")
    break
  except Exception as e: 
    traceback.print_exc()
    fail("Global: %s"%e)
    time.sleep(3)
    continue
  