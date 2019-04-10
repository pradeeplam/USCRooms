# USC Rooms
Web scraper and command line tool to find empty rooms at USC

Setup: 

Run setup.py with USC class catalog URL (Ex. https://classes.usc.edu/term-20191/)

Will create/delete multiple temp files and create a permanent .pickle file

Using room.py:

To look up room's schedule: room.py <Building> <Room #>
|-> Ex. room.py VKC 204

To look up free room for particular time:
room.py <Day of Week> <Start Time> <Duration in Hr>
|-> Ex. room.py M 10:30AM 2