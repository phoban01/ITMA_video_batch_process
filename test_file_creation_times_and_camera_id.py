import os,fnmatch,subprocess,time
import re
from time import gmtime,strftime
from datetime import datetime

def creation_time(path):
	t = os.path.getmtime(path)
	time_data = {}
	FMT = '%d %B %Y @ %H:%M:%S'
	time_string = time.strftime(FMT,time.gmtime(t))
	time_data['day'] = time_string.split()[0]
	time_data['month'] = time_string.split()[1]
	time_data['year'] = time_string.split()[2]
	time_data['date'] = ' '.join(time_string.split()[0:3])
	time_data['time'] = time_string.split()[4]
	time_data['full'] = time_string
	time_data['FMT'] = FMT
	return time_data

def modification_date(filename):
	t = os.path.getmtime(filename)
	return datetime.fromtimestamp(t)

def get_camera_id(filename):
	string = subprocess.Popen(["ffprobe",filename],stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()[-1]
	match = re.search("(uid\s+: \S*)",string).groups()[0].split()[-1]
	camera_id = match.split('-')[-1][-7:]
	return camera_id

def get_duration_in_seconds(mxf_file):
	duration = float(subprocess.check_output(["ffprobe","-v","quiet","-print_format","compact=print_section=0:nokey=1:escape=csv","-show_entries","format=duration",mxf_file]))
	return duration

def time_group(lst,limit=0.25):
	'''Limit is time limit in hours between separate events'''
	mxf_file_durations = []
	print 'Getting MXF durations...'		
	for i,x in enumerate(lst):
		mxf_file_durations.append(get_duration_in_seconds(x))
	print 'Calculating groups...'		
	groups = []
	g = [lst[0]]
	last_cid = get_camera_id(lst[0])
	for i in range(1,len(lst)):
		x = creation_time(lst[i])
		y = creation_time(lst[i-1])
		delta = datetime.strptime(x['full'],x['FMT']) - datetime.strptime(y['full'],y['FMT'])
		delta_hours = (delta.total_seconds() / 60) / 60
		cid = get_camera_id(lst[i])
		# this removes duplicate events
		if delta_hours != 0:
			# create a new group when time limit is exceeded and the camera id changes
			if delta_hours < limit and cid == last_cid:
				g.append(lst[i])
			else:
				groups.append(g)
				g = [lst[i]]
		last_cid = cid
	groups.append(g)
	second_pass_groups = []
	# remove any groups whose duration is shorted than 30 seconds
	for i,group in enumerate(groups):
		durs = [mxf_file_durations[lst.index(j)] for j in group]
		total_group_duration = sum(durs)
		print total_group_duration
		if total_group_duration > 30:
			second_pass_groups.append(group)		
	return second_pass_groups

source = "/Volumes/ITMADATA/VIDEO/ITMA video field recordings/in process/ITMA field recordings of William Kennedy Piping Festival Nov 2014/"
# source = "/Volumes/ITMADATA/VIDEO/ITMA video field recordings/in process/Goodman Trio ITMA Nov 2014"
files= []

for root,dirnames,filenames in os.walk(source):
	for filename in fnmatch.filter(filenames,'*.MXF'):
		files.append(os.path.join(root,filename))

files.sort(key=lambda x:modification_date(x))
files.sort(key=lambda x:x.split('/')[-1])

items = time_group(files)

print len(items)


