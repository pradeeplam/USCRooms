'''
Usage:
- Run w/ source URL "Schedule of Classes" for current semester (Ex. https://classes.usc.edu/term-20191/)
- Run before room.py
- Single run should configure everything for room.py to run

Notes: 
- If scaper crashes midway, wait for some time and then rerun the program
- Program meant to crash "safely"
  What that means:
	- One function failing -> Crash -> Fix and rerun -> Shouldnt have to delete or redownload files/dir
	- If a function is wrong...However..May have to restart from scratch
- Program should only work with times 5AM to 11PM

Disclamer:
- Treat nicely - Hasn't been dumbass proofed - I'm sure you can break it if you tried
- The scraper, collation, and clean functions will have to be modified if the USC source website is ever changed
'''

from bs4 import BeautifulSoup
from urllib.request import urlopen
import sys
import shutil
import os
import pandas as pd
import re
import numpy as np
import pickle

'''
Purpose: Download documents from web

Notes:
- Another method may need to be employed to scrape this data in the future
- This method has recently been unreliable

'''
def scrape(start_url):

	# Because scraper is known to crash at times ..
	# Don't want to re-scrape for info we already have
	pre_crash = []

	if os.path.isfile('./data_temp.csv'):
		print("Skipping scrape!")
		return

	if os.path.exists("./data_temp/"):
		pre_crash = os.listdir("./data_temp/")
		pre_crash = [file.split(".")[0] for file in pre_crash]
	else:
		os.makedirs("./data_temp")

	startPage = urlopen(start_url)
	soup = BeautifulSoup(startPage,"lxml")

	# Grab the list-item elements from table which correspond to departments
	list_item = soup.findAll("li", {"data-type" : "department"}) 

	# 1. Extract url for department
	# 2. Extract document link from department page
	# 3. Download document

	count = 0

	for l in list_item:
		count += 1

		# Extract url from list-item
		dept_link = l.find('a',href=True)['href']
		
		# Check if needs to be parsed
		dept_name = dept_link.split("/")[-2] # Link ends w a "/"

		# Skip dept
		if dept_name in pre_crash:
			print("Skipping - File found: " + dept_name + ".csv")
			continue			

		dept_page = urlopen(dept_link)
		soup = BeautifulSoup(dept_page,"lxml")

		dload_link = soup.find('a',href=True,text="Download as a spreadsheet")
	
		if dload_link == None:
			print(str(dept_name) + ": Has No Summary Document")

		else:
			dload_link = dload_link['href']

			# Open & save file in "data_temp" dir
			with urlopen(dload_link) as response, open("./data_temp/"+dept_name+".csv", 'wb') as out_file:
				shutil.copyfileobj(response, out_file)

			print(str(count) + " of " + str(len(list_item)) + " Complete: " + dept_name)


	print("Finished scraping!")

'''
Purpose: Take folder w/ many different schedule csv files and collate into a single csv file.

Notes:
- A bit of cleaning performed for the purpose of collatation
- An attempt is made to correct 2 of the most common problems 
  found so far in these csv files
- Other problems will need to be corrected manually
- Program running perfectly will result in only 1 file being in data_temp (all.csv)
'''
def collate():
	if os.path.isfile("./data_temp.csv"):
		print("Skipping collate!")
		return

	files = os.listdir("./data_temp/")

	data = pd.DataFrame()

	for file in files:

		with open("./data_temp/"+file,"r") as fp:
			text = fp.read()

		# If file empty 
		if len("".join(text.split())) == 0: # NOT stupid - Need to check for white space
			print("Error - Empty file: " + file)
			continue

		# URLs rofessors sometimes have "," in them
		# Messes up pandas parsing
		text = text.replace(",<","<")

		# Easiest way to then read data into pandas DF
		with open("./data_temp/"+file,"w") as fp:
			fp.write(text)
	
		try: # Try to read csv file
			toAppend = pd.read_csv("./data_temp/"+file)

		except: # Not anticipated error
			print("Error - Format error: " + file)

		else: # Everything worked out fine
			data = data.append(toAppend)
			print("Combined: " + file)


	data.to_csv("./data_temp.csv", index=False)

	# Delete all files
	for file in files:
		os.remove("./data_temp/"+file) 

	# Delete empty dir
	os.rmdir("./data_temp/")

	print("Finished collating!")

'''
Purpose: Get rid of irrelevant rows/cols.

Can delete all col EXCEPT:
1. Time 2. Days 3. Room

Can delete row IF:
1. Nan-values/TBA in Time, Days or Room
2. Room marked as OFFICE 
3. Den@Viterbi
'''

def scrub():
	data = pd.read_csv("./data_temp.csv")

	# Basic cleaning
	data = data[["Time","Days","Room"]] 

	data.dropna(inplace=True)

	# Not places in the physical plane
	data = data[~data["Time"].str.contains("TBA")]
	data = data[~data["Days"].str.contains("TBA")]
	data = data[~data["Room"].str.contains("TBA")]
	data = data[~data["Room"].str.contains("OFFICE")]
	data = data[~data["Room"].str.contains("ONLINE")]
	data = data[~data["Room"].str.contains("DEN@Viterbi")]
	data = data[~data["Room"].str.contains("VAC")]

	# Uuuh.. Not sure what these are
	data = data[~data["Room"].str.contains("NCT")]
	data = data[~data["Room"].str.contains("CENTER")]
	data = data[~data["Room"].str.contains("TTL")]
	data = data[~data["Room"].str.contains("BIT")]

	data = data.drop_duplicates()

	data.to_csv("./data_temp.csv", index=False)

	print("Finished scrubbing irrelevant rows/cols!")

'''
Purpose: Put data into format which can be easily queried.

- Some cleaning is done for this purpose

'''
def makeQueryable():
	data = pd.read_csv("./data_temp.csv")

	# Sometimes, multiple rooms are listed for the same day/time period
	# Ambiguous
	# Need to seperate - Let's just assume all rooms are used for entire time period

	to_split = data[data["Room"].str.contains(",")]
	data = data[~data["Room"].str.contains(",")]  # Remove these entries from the dataset

	# Append to original as seperate rows
	for _, row in to_split.iterrows():
		rooms = row["Room"].split(",")

	# Duplicate over rooms 
	for room in rooms:
		data = data.append({'Time': row["Time"], 'Days':row["Days"], 'Room':room.strip()}, ignore_index=True)

	# Reset all the columns indices
	data = data.reset_index()

	# Standardize days 
	# Create seperate rows per day

	cleaned = pd.DataFrame()

	# Append to new dataframe as seperate rows
	for _, row in data.iterrows():

		days = []
		
		for day in ["M","Tu","W","Th","F","Sa","Su"]:
			if day in row["Days"]:
				days.append(day)

		# Duplicate over days 
		for day in days:
			cleaned = cleaned.append({'Time': row["Time"], 'Days':day, 'Room':row["Room"]}, ignore_index=True)

	# 3-Layer dict
	# Layer 1: Days of week
	# Layer 2: Buildings
	# Layer 3: Rooms
	# Value: Bit-np-array

	data_dict = {"M":{},"Tu":{},"W":{},"Th":{},"F":{},"Sa":{},"Su":{}}

	for _, row in cleaned.iterrows():
		day = row["Days"]

		# Need to partition Room string into building and room number
		# String format is either <String><Space><String> or <String><Int>
		room_str = row["Room"]

		if len(room_str.split()) == 2:
			build, num = room_str.split()
		elif "STG" in room_str:
			build, num = room_str.split("STG")
			num = "STG" + num
		else:
			if re.search("\d",room_str) == None:
				print(room_str)
			fni = re.search("\d",room_str).start() # Location of 1st number
			build = room_str[:fni]
			num = room_str[fni:]

		build = build.strip()
		num = num.strip()

		# Init new buildings
		if build not in data_dict[day].keys():
			for d in ["M","Tu","W","Th","F","Sa","Su"]:
				data_dict[d][build] = {}

		# Init new rooms
		if num not in data_dict[day][build].keys():
			for d in ["M","Tu","W","Th","F","Sa","Su"]:
				data_dict[d][build][num] = np.zeros(216, dtype=bool) # Eeh..Feels bad for hardcoding..

		start,end = row["Time"].split("-")
		start_hr, start_min = start.split(":") 
		end_hr, end_min = end.split(":")

		# Need to parse away am/pm from end_hr
		ap = end_min[-2:]
		end_min = end_min[:-2]

		start_hr, start_min, end_hr, end_min = int(start_hr), int(start_min), int(end_hr), int(end_min)

		# Standardize such that right_hr is always > left_hr

		# Have to standardize only end_hr
		if start_hr > end_hr: # Ex: 11:00-1:00pm means 11:00am-1:00pm 
			end_hr += 12	

		# Have to standardize both start_hr & end_hr
		elif ap == "pm" and end_hr != 12: # 12pm falls into category above but you don't have to correct for it
			start_hr += 12
			end_hr += 12

		# Create a bit representation of time

		# Round to nearest 5 minutes (Round down)
		start_min -= start_min % 5
		end_min -= end_min % 5

		duration = np.zeros(216, dtype=bool) # Eeh..Feels bad for hardcoding..

		# Schedule starts at 5:00AM
		start = ((start_hr - 5)*60)/5 + start_min/5
		start = int(start)

		# Schedule starts 5:00AM (Won't make it right - Just won't crash)
		if start < 0:
			start = 0

		# End time 
		end = start + ((60*end_hr + end_min) - (60*start_hr + start_min))/5
		end = int(end)

		# Schedule ends 11:00PM (Won't make it right - Just won't crash)
		if end > 216: # Eeh..Feels bad for hardcoding..
			end = 216

		duration[start:end] = True

		# Reserve time 
		data_dict[day][build][num] |= np.logical_or(data_dict[day][build][num], duration)

	# Save dict to file
	with open('data.pickle', 'wb') as handle:
		pickle.dump(data_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)

	# Can remove original file
	# os.remove("./data_temp.csv") 

	print("Finished setup!")

if __name__ == "__main__":
	
	if len(sys.argv) != 2:
		print("Usage: python3 setup.py <Starter URL>")
		exit()

	scrape(sys.argv[1])
	collate()
	scrub()
	makeQueryable()

