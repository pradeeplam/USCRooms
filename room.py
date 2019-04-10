'''
Usage:
- Can use this program to lookup the schedule of a particular room or find a room for a particular time
- Only have data on rooms which have classes at some point

Notes: 
- Program should only work with times 5AM to 11PM

Disclamer:
- Treat nicely - Hasn't been dumbass proofed - I'm sure you can break it if you tried
'''

import sys
import pickle
import numpy as np
import random

# Turn an array of booleans into something I can read 
# Return formatted string
def makeReadable(start, end):
	# Convert start and end time into start and end bit locations

	start_hr = 5 + int(start / 12) # Eeh..Feels bad for hardcoding..
	start_min = (start % 12)*5

	end_hr = 5 + int((end + 1) / 12) 
	end_min = ((end + 1) % 12)*5

	start_suffix = "AM"
	end_suffix = "AM"

	# Correct for AM/PM
	if start_hr > 12:
		start_hr -= 12
		start_suffix = "PM"

	if start_hr == 12:
		start_suffix = "PM"

	if end_hr > 12:
		end_hr -= 12
		end_suffix = "PM"

	if end_hr == 12:
		end_suffix = "PM"

	start_hr, start_min, end_hr, end_min = str(start_hr), str(start_min), str(end_hr), str(end_min) 

	if int(start_min) < 10:
		start_min =  "0" + start_min

	if int(end_min) < 10:
		end_min = "0" + end_min

	return start_hr + ":" + start_min + start_suffix + " to " + end_hr + ":" + end_min + end_suffix 

# Print usage schedule for a given room
def lookupRoom(build, room, data_dict):

	day_schedule = {}

	for day in ["M","Tu","W","Th","F","Sa","Su"]:
		day_schedule[day] = data_dict[day][build][room]

	print("\n\nLoc: " + build + " " + room)
	print("Schedule: \n")

	# Convert to human readable
	whole = {"M":"Monday","Tu":"Tuesday","W":"Wednesday","Th":"Thursday","F":"Friday","Sa":"Saturday","Su":"Sunday"}

	# Iterate through days
	for day in ["M","Tu","W","Th","F","Sa","Su"]:
		print(whole[day] + ":")

		pos = np.argwhere(day_schedule[day] == 1).flatten()

		if len(pos) == 0:
			print("No info: No classes listed for day.\n\n")
			continue

		pos = pos.tolist()

		start = pos[0] # First
		end = pos[-1] # Last

		# Iterate through chunks 
		for i in range(len(pos)):

			if i == len(pos) - 1 or pos[i+1] - pos[i] > 1:
				end = pos[i]
				
				print(makeReadable(start,end))

				if i != len(pos) - 1:
					start = pos[i + 1]
		
		print("\n")

# Find available rooms for a particular time period
# 2 classes of rooms - Rooms I commonly use - All other options

def lookupTime(day, time, dur, data_dict):

	# Convert input to workable
	hr, m = time.split(":")

	am_pm = m[-2:]
	m = m[:-2]

	hr, m = int(hr), int(m)

	if am_pm == "PM" and hr != 12:
		hr += 12

	# Make a comparable np boolean array from time specs
	converted = np.ones(216, dtype=bool) # Eeh..Feels bad for hardcoding..s

	start = ((hr - 5)*60)/5 + m/5
	start = int(start)

	end = start + 12*int(dur)

	converted[start:end] = False

	# Collection stage
	saved = []

	# Iterate through entire dict and find entries which fit with comparable 
	for build in data_dict[day].keys():
		for room in data_dict[day][build].keys():

			together = ~np.logical_or(data_dict[day][build][room], converted)
			
			if together.sum() >= 12 : # If there's at least an hour of overlap
				pos = np.argwhere(together == 1).flatten()

				pos = pos.tolist()

				start = pos[0] # First
				end = pos[-1] # Last

				# Overlap can be over multiple components
				# For longer periods of time, there may be a class in between multiple avail periods
				parts = ""
				# Iterate through chunks
				for i in range(len(pos)):
					if i == len(pos) - 1 or pos[i+1] - pos[i] > 1:
						end = pos[i]
						parts += makeReadable(start,end) 

						if i != len(pos) - 1:
							parts += "|"
							start = pos[i + 1]

				saved.append((build,room, i, parts)) # Saving i for sorting purposes

	# Print stage

	# Split output into popular and other
	most_used = [element for element in saved if element[0] in ["THH", "VKC", "ANN", "GFS"]]
	others = [element for element in saved if element[0] not in ["THH", "VKC", "ANN", "GFS"]]


	if len(most_used) > 10:
		most_used = [ most_used[i] for i in sorted(random.sample(range(len(most_used)), 10)) ]

	if len(others) > 10:
		others = [ others[i] for i in sorted(random.sample(range(len(others)), 10)) ]

	most_used = sorted(most_used, key=lambda x: (x[0], x[1], x[2]))
	others = sorted(others, key=lambda x: (x[0], x[1], x[2]))
	
	print("\n\nPopular Buildings:")

	if len(most_used) == 0:
		print("No rooms meet criteria.")

	for element in most_used:
		build, room, _, parts = element
		print(build + " " + room)

		for each in parts.split("|"):
			print(each)

	print("\n\nRandom Buildings:")

	if len(others) == 0:
		print("No rooms meet criteria.")

	for element in others:
		build, room, _, parts = element
		print(build + " " + room)

		for each in parts.split("|"):
			print(each)

	print("\n")

if __name__ == "__main__":
		
	if len(sys.argv) < 3: 	
		print("Usage:")
		
		print("Room Lookup: python3 room.py <Building> <Room #>")
		print("Note: All caps for building\n\n")

		
		print("Time Lookup: python3 room.py <Day of Week> <Start Time> <Duration>")
		print("Format for Day: M, Tu, W, Th, F, Sa, Su")
		print("Format Ex for Time: 10:30AM")

		exit()

	with open('./data.pickle', 'rb') as handle:
		data_dict = pickle.load(handle)
	
	# Assume time lookup
	if sys.argv[1] in ["M","Tu","W","Th","F","Sa","Su"]:

		day = sys.argv[1]
		time = sys.argv[2]
		dur = sys.argv[3]
		
		lookupTime(day, time, dur, data_dict)



	# Assume room lookup
	else:

		build = sys.argv[1]
		room = sys.argv[2]

		# Ex. Stage A
		if len(sys.argv) == 4:
			room += " " + sys.argv[3]


		# Check if valid
		if build in data_dict["M"].keys() and room in data_dict["M"][build].keys():
			lookupRoom(build, room, data_dict)

		else:
			print("Error: Invalid building or room.")
