# Batch process raw MXF files from Canon 
# Create master MXF file and DVD-ready MP4 file for each event in field recording trip
# Events are defined as sequential groups of recordings separated by a minimum time-limit
# Minimum time limit is specified in hours.
# 0.25 hours (15 minutes between events) is default



# NOT ABLE TO DISTINGUISH BETWEEN SHORT EVENTS AND POST-INTERVAL EVENTS YET... 
# SO NOT USEFUL

import os,subprocess,sys,time,logging
from datetime import datetime
from time import gmtime,strftime,strptime

from progressbar import Bar,Percentage,ProgressBar

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

def get_duration(item):
	time_counter = 0
	for mxf_file in item:
		duration = float(subprocess.check_output(["ffprobe","-v","quiet","-print_format","compact=print_section=0:nokey=1:escape=csv","-show_entries","format=duration",mxf_file]))
		time_counter += duration
	return time.strftime('%R:%S',time.gmtime(time_counter))

def get_duration_in_seconds(mxf_file):
	duration = float(subprocess.check_output(["ffprobe","-v","quiet","-print_format","compact=print_section=0:nokey=1:escape=csv","-show_entries","format=duration",mxf_file]))
	return duration


# use two-pass
# first split based on time limit
# then check duration of new files.
# if duration of one file is 30 minutes or less
# and separation between previous event is less than time
def time_group(lst,limit=0.25):
	'''Limit is time limit in hours between separate events'''
	groups = []
	g = [lst[0]]
	print lst[0]
	mxf_file_durations = []
	inter_event_times = [0]
	print 'Getting MXF durations...'	
	with ProgressBar(widgets=[Percentage(), Bar()],maxval=len(lst), redirect_stdout=True) as p:
		for i,x in enumerate(lst):
			mxf_file_durations.append(get_duration_in_seconds(x))
			p.update(i)
	for i in range(1,len(lst)):
		x = creation_time(lst[i])
		y = creation_time(lst[i-1])
		delta = datetime.strptime(x['full'],x['FMT']) - datetime.strptime(y['full'],y['FMT'])
		delta_hours = (delta.total_seconds() / 60) / 60
		if delta_hours < limit:
			g.append(lst[i])
		else:
			groups.append(g)
			g = [lst[i]]
			inter_event_times.append(delta_hours)
	groups.append(g)
	second_pass_groups = []
	print inter_event_times
	for i,group in enumerate(groups):
		durs = [mxf_file_durations[lst.index(j)] for j in group]
		total_group_duration = sum(durs) / 60 / 60
		# if duration of group is less than 1 hour 45
		# && if time interval between this and last event is less than ~40 minutes
		# then add this groups files to previous group 
		# these limits should be enough to do "smart" grouping?
		if i != 0 and total_group_duration < 1.75  and inter_event_times[i] < 0.66:
			second_pass_groups[-1].extend(group)
		else:
			second_pass_groups.append(group)
	print len(groups),len(second_pass_groups)
	return second_pass_groups

def get_mxf_files(path):
	mxfers = []
	for r,d,f in os.walk(path):
		for fx in f:
			if fx.endswith('.MXF'):
				mxfers.append(r+'/'+fx)
	return mxfers


def process_folder(path):
	event_name = path.split('/')[-1]
	mxf_files = get_mxf_files(path) 
	mxf_files.sort(key=lambda x:creation_time(x))
	if len(mxf_files) > 0:
		items = time_group(mxf_files)
	else:
		print "Found No MXF Files => %s"%path


def main():
	card_folders = [ROOT+'/'+f for f in os.listdir(ROOT) if os.path.isdir(ROOT+'/'+f)]
	for i in card_folders[1:2]:
		print i.split('/')[-1]
		process_folder(i)

# probably still needs checking to ensure that MXF files are re-written where necessary if things fail?

ROOT = "/Volumes/ITMADATA/VIDEO/ITMA video field recordings/in process"

time_limit = None

if __name__ == '__main__':
	main()
