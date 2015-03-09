import os, sys, re, time
import urllib2
from bs4 import BeautifulSoup


#Set the class to mine the scores
class MineScore:
	
	espn_cricinfo_url = "http://www.espncricinfo.com"


	@staticmethod
	def set_buffer(pageURL):
		soup = BeautifulSoup(urllib2.urlopen(pageURL).read())
		return soup


	#set an object for the page given. put the details in that object
	def fetch_page_details(self):
		try :
			pager = MineScore.set_buffer(self.page)
			return (0, pager)
		except Exception as e:
			print sys.exc_info()[0], e
			return (-1, "Not able to fetch page details")


	#gets the information of the match venue and redirects to match page
	def fetch_current_match_urls(self):
		try :
			match_info_url = "http://www.espncricinfo.com/ci/engine/match/index.html?date="
			match_info_url += time.strftime("%Y-%m-%d") #get the date to append to match info url and start fetching individual match urls to get scores
			#match_info_url += "2015-02-14"
			match_getter = MineScore.set_buffer(match_info_url)
			match_getter.prettify()

			match_type = (match_getter.find(class_="match-section-head").text).strip()

			#get the One-Day International matches list
			if match_type == "One-Day Internationals" :
				#get those matches live scores url
				match_href_val = "/icc-cricket-world-cup-2015/engine/match"
				match_hrefs = match_getter.findAll('a', href=re.compile(match_href_val), text=re.compile('Live scorecard'))
				
				#get the match_urls in a list and store it there
				match_urls = []
				for match_href in match_hrefs :
					match_urls.append(str(MineScore.espn_cricinfo_url + match_href.get('href')))

				#may be write an intelligence which will return the currently running match details only!				
				for m_url in match_urls :
					MineScore.fetch_indiv_match_info(m_url)
				#MineScore.fetch_indiv_match_info("http://www.espncricinfo.com/icc-cricket-world-cup-2015/engine/match/656403.html")
				#if score A is already available a simple math can do the trick for us! use that innings-requirement tag
			else :
				return (-1, "No Match today!")
		except Exception as e:
			print sys.exc_info()[0], e
			return (-1, "Not able to fetch anything from this page")


	@staticmethod
	def fetch_indiv_match_info(match_url):
		#now fetch the individual score details from those links you obtained above.
		team_A = team_B = runs = wickets = overs = None

		score_info_getter = MineScore.set_buffer(match_url)
		score_info_getter.prettify()
		#get the team names and scores
		team_A = score_info_getter.find(class_="team-1-name").text.strip()
		team_B = score_info_getter.find(class_="team-2-name").text.strip()

		innings_req = score_info_getter.find(class_='innings-requirement').text.strip()
		meta_score_tag = score_info_getter.find('title').text.strip()
		#innings_req can contain some of these common strings
		#won, the, toss - indicates first innings is on or almost done
		#require, runs, wickets, remaining - indicates second innings is on.
		#we can even fetch innings= data from the page but that is for another day as lot of url dividing needs to be done
		team_A_list = [str(x) for x in team_A.split(" ")]
		team_B_list = [str(x) for x in team_B.split(" ")]
		innings_req_list = [str(x) for x in innings_req.split(" ")]


		print innings_req_list[:len(team_A_list)]
		team = ""
		if team_A in innings_req:
			team = team_A
		elif team_B in innings_req:
			team = team_B
			
		status, innings, runs_1, runs_2, wickets, overs, balls = MineScore.check_current_innings_status(score_info_getter,team, innings_req_list)


	@staticmethod
	def check_current_innings_status(score_info_getter, team, innings_req_list):

		if "Match scheduled to begin in " in " ".join(innings_req_list) :
			status = " ".join(innings_req_list)
		else :		
			meta_score_tag = score_info_getter.find('title').text.strip()
			meta_score_tag_list = meta_score_tag.split(" ")
			runs_1 = 0
			runs_2 = 0
			overs = 0
			balls = 0
			innings = 0
			wickets = 0
			status = 0
			if "won" in innings_req_list :
				if "toss" in innings_req_list :
					innings = 1
					if "field" in innings_req_list :
						status = "field"
						runs_2 = int(meta_score_tag_list[1].split("/")[0]) #if teamA is fielding, the score will goto teamB
						wickets = int(meta_score_tag_list[1].split("/")[1])
					elif "bat" in innnings_req_list :
						status = "bat"
						runs_1 = int(meta_score_tag_list[1].split("/")[0]) #if teamA is batting, the score will remain for teamB
					
					wickets = int(meta_score_tag_list[1].split("/")[1])
					overs_or_balls = meta_score_tag_list[2][1:]
					if "." in overs_or_balls :
						overs, balls = map(int, overs_or_balls.split("."))
					else :
						balls = int(overs_or_balls) % 6
						overs = int(overs_or_balls) / 6

				else :
					status = " ".join(innings_req_list)
			elif "require" in innings_req_list and "another" in innings_req_list and "runs" in innings_req_list and "wickets" in innings_req_list and "remaining" in innings_req_list :
				status = "chasing"
				innings = 2
				runs_2 = int(meta_score_tag_list[1].split("/")[0])
				runs_1 = int(innings_req_list[innings_req_list.index("runs") - 1]) + runs_2 -1
				wickets = int(meta_score_tag_list[1].split("/")[1])
				overs_or_balls_remaining = (innings_req_list[innings_req_list.index("remaining") - 2]) #cos the string before 'remaining' might have overs or balls. 
				if "." in overs_or_balls_remaining :
					overs, rem_balls = [int(x) for x in overs_or_balls_remaining.split(".")]
					rem_balls += overs*6
					balls = int(300 - rem_balls) / 6
					overs = int(300 - rem_balls) % 6

			return status, innings, runs_1, runs_2, wickets, overs, balls

