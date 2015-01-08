# Batch process raw MXF files from Canon 
# Create master MXF file and DVD-ready MP4 file for each event in field recording trip
# Events are defined as sequential groups of recordings separated by a minimum time-limit
# Minimum time limit is specified in hours.
# 0.25 hours (15 minutes between events) is default

# further error checking...
# Sometime the same card data has been uploaded twice into different folders
# 

# updated so that files are grouped by camera id, to avoid interleaving things recorded at the same time
# on different cameras.

# also files under a minimum duration are discarded

import os,subprocess,sys,time,logging,re
from datetime import datetime
from time import gmtime,strftime

def is_too_old(path):
	global cut_off_date
	if cut_off_date != None:
		input_date_obj =  datetime.strptime(cut_off_date,'%d/%m/%Y')
		datestr = [int(x) for x in cut_off_date.split('/')]
		t = os.path.getmtime(path)
		FMT = '%d/%m/%Y'
		time_string = time.strftime(FMT,time.gmtime(t))
		time_string = datetime.strptime(time_string,'%d/%m/%Y')
		delta = (time_string - input_date_obj).days < 0
		return delta
	else:
		return False

def disk_usage(path):
    st = os.statvfs(path)
    free = st.f_bavail * st.f_frsize
    total = st.f_blocks * st.f_frsize
    used = (st.f_blocks - st.f_bfree) * st.f_frsize
    return used/float(total)

def check_disk_usage(limit=0.925):
	global OUTPUT_DIRECTORY
	global write_disk_index
	global write_disks
	
	switched = False

	if disk_usage(OUTPUT_DIRECTORY) > limit:
		if write_disk_index == 0 and len(write_disks) > 1:
			write_disk_index += 1
			OUTPUT_DIRECTORY = write_disks[write_disk_index]
			switched = True
			print 'No more disk space available on: %s. \nSwitching to disk:%s \nSwitched at %s' % (write_disks[write_disk_index-1],write_disks[write_disk_index],strftime("%H:%M:%S | %Y-%m-%d",gmtime()))
		else:
			print 'No more write space on either disk. Process stopping at:%s' % strftime("%H:%M:%S | %Y-%m-%d",gmtime())
			exit()
	return switched

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

def get_camera_id(filename):
	string = subprocess.Popen(["ffprobe",filename],stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()[-1]
	match = re.search("(uid\s+: \S*)",string).groups()[0].split()[-1]
	camera_id = match.split('-')[-1][-7:]
	return camera_id

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
	# remove any groups whose duration is shorted than 3 minutes
	for i,group in enumerate(groups):
		durs = [mxf_file_durations[lst.index(j)] for j in group]
		total_group_duration = sum(durs)
		if total_group_duration > 180:
			second_pass_groups.append(group)		
	return second_pass_groups

def get_mxf_files(path):
	mxfers = []
	for r,d,f in os.walk(path):
		for fx in f:
			if fx.endswith('.MXF') and not fx.startswith('.'):
				filepath = os.path.join(r,fx)
				# remove any files that are older than the cutoff date
				if is_too_old(filepath) == False:
					mxfers.append(filepath)
	return mxfers

def get_names(path):
	subfolders = [x for x in os.listdir(path) if not x.startswith('.')]
	names = []
	if any([x.startswith('AA') for x in subfolders]):
		names.append(path.split('/')[-1].replace(' ','_').replace(',',''))
	elif any([x for x in subfolders if not x.find('card') == -1]):
		for x in subfolders:
			name = path.split('/')[-1].replace(' ','_').replace(',','') + '_' + x.replace(' ','_')
			names.append(name)
	elif len(subfolders) == 1:
		names.append(path.split('/')[-1].replace(' ','_').replace(',',''))
	else:
		for x in subfolders:
			name = x.replace(',','').replace(' ','_')
			names.append(name)
	names.sort()
	names = [x.lower() for x in names]
	return names

def get_duration(item):
	time_counter = 0
	for mxf_file in item:
		duration = float(subprocess.check_output(["ffprobe","-v","quiet","-print_format","compact=print_section=0:nokey=1:escape=csv","-show_entries","format=duration",mxf_file]))
		time_counter += duration
	return time.strftime('%R:%S',time.gmtime(time_counter))

def get_duration_in_seconds(mxf_file):
	duration = float(subprocess.check_output(["ffprobe","-v","quiet","-print_format","compact=print_section=0:nokey=1:escape=csv","-show_entries","format=duration",mxf_file]))
	return duration

def write_file_lists(items,output_path,event_name):
	paths = []
	for i,event in enumerate(items):
		mp4_path = output_path + "/MP4/" + event_name.replace(' ','_') + "_event_%s.mp4" % (i+1)
		fl_path = output_path + event_name.replace(' ','_') + "_event_%s.txt" % (i+1)
		# does mp4 file exist? if so does .txt file exist?
		# if not don't include this in file list		
		if os.path.exists(mp4_path) and not os.path.exists(fl_path):
			print "This File Has Already Been Completed: %s_%s" % (event_name,i+1)
		else:	
			paths.append(fl_path)
			event_file_list = open(fl_path,"w")
			for i in event:
				event_file_list.write("file %s\n" % i.replace(' ','\ ').replace("'","\\'"))
			event_file_list.close()
	return paths

def write_metadata_file(event_name,output_path,items,path,names):
	if not os.path.exists(output_path+"folder_metadata.txt"):
		print "Writing Metadata for %s" % event_name 
		data_file = open(output_path+"folder_metadata.txt","w")
		data_file.write("%%%%% Metadata for folder: {0} %%%%% \n\n".format(event_name))
		data_file.write('SOURCE: %s\n\n'%path)
		data_file.write('ITEMS: %s\n\n'%len(items))
		data_file.write('\nCREATED ON:\n')
		for i,obj in enumerate(items):
			data_file.write('\tITEM %s: %s %s \n'%(i+1,creation_time(obj[0])['date'],creation_time(obj[0])['time']))
		data_file.write("\nCONTENTS DURATIONS:\n")
		for i,obj in enumerate(items):
			data_file.write('\tITEM %s Duration:%s\n'%(i+1,get_duration(obj)))
		data_file.write("\nTHE FOLLOWING NAMES WERE FOUND:\n")
		for i,obj in enumerate(names):
			data_file.write("\t%s: %s\n\n"%(i+1,obj))
		data_file.write("\n%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
		data_file.close()
		print "Metadata Written"
	else:
		print "Metadata File Already Exists"
	return None

def make_mxf(lst_file,mxf_file_name):
	global time_limit
	ffmpeg_cmd = ["ffmpeg", 
				# overwrite [y] / don't overwrite [n]
				"-n",
				"-f","concat",
				"-i",lst_file,
				"-map","0",
				"-c","copy",
				"-ac","2",
				# "-v","quiet",	
				]
	if time_limit != None:
		ffmpeg_cmd.append("-t")
		ffmpeg_cmd.append(str(time_limit))
	ffmpeg_cmd.append(mxf_file_name)
	return ffmpeg_cmd


def make_mp4(mxf_file_name,mp4_file_name,mxf_duration):
	global time_limit
	# 8192kb = 1MB
	# 1000MB = 1GB
	ideal_file_size = 4499 * 8192
	audio_bit_rate = 320
	# ?=> audio bit rate times two because audio is stereo -this doesn't seem necessary?
	# finder file size is > 4.7 but ls -lah shows files are ok.
	video_bitrate = int((ideal_file_size / mxf_duration) - audio_bit_rate)
	# print video_bitrate
	# first pass
	ffmpeg_cmd = ["ffmpeg", 
				"-y",
				"-i",mxf_file_name,
				"-c:v",'libx264',
				"-preset","veryfast",
				"-b:v",str(video_bitrate)+'k',
				"-pix_fmt","yuv420p",				
				"-pass","1",
				"-c:a","libfdk_aac",
				"-map","0",
				"-b:a",str(audio_bit_rate)+'k',
				# "-v","quiet",
				"-ac","2",				
				"-f","mp4",
				]
	ffmpeg_cmd.append("/dev/null")
	print '--> Executing first pass MP4 File %s | %s' % (mp4_file_name,strftime("%H:%M:%S | %Y-%m-%d",gmtime()))
	shellCmd = subprocess.Popen(ffmpeg_cmd)
	shellCmd.wait()
	# second pass
	ffmpeg_cmd = ["ffmpeg", 
				"-y",
				"-i",mxf_file_name,
				"-c:v",'libx264',
				"-preset","veryfast",
				"-b:v",str(video_bitrate)+'k',
				"-pix_fmt","yuv420p",				
				"-pass","2",
				"-c:a","libfdk_aac",
				"-map","0",				
				"-b:a",str(audio_bit_rate)+'k',		
				"-ac","2",
				# "-v","quiet",
				]
	ffmpeg_cmd.append(mp4_file_name)
	print '--> Executing second pass MP4 File %s | %s' % (mp4_file_name,strftime("%H:%M:%S | %Y-%m-%d",gmtime()))
	shellCmd = subprocess.Popen(ffmpeg_cmd)	
	shellCmd.wait()

def process_folder(path):
	global OUTPUT_DIRECTORY,event_count
	event_name = path.split('/')[-1]
	print "================\nINFO: Processing %s" % event_name
	output_path = OUTPUT_DIRECTORY + event_name + '/'
	mxf_files = get_mxf_files(path) 
	# sort first by time
	mxf_files.sort(key=lambda x:creation_time(x))
	# sort secondly by file sequence number
	mxf_files.sort(key=lambda x:x.split('/')[-1])
	if len(mxf_files) > 0:
		items = time_group(mxf_files)
		event_count += len(items)
		names = get_names(path)
		if not os.path.exists(output_path):
			os.mkdir(output_path)
		write_metadata_file(event_name,output_path,items,path,names)	
		paths = write_file_lists(items,output_path,event_name)
		if len(paths) > 0:
			for lst_file in paths:
				# check if enough disk-space is left : returns True if a switch has occured.
				if check_disk_usage(0.98) == True:
					output_path = OUTPUT_DIRECTORY + event_name + '/'
					if not os.path.exists(output_path):
						os.mkdir(output_path)
				if not os.path.exists(output_path+'/MXF'):
					os.mkdir(output_path+'/MXF')	
				if not os.path.exists(output_path+'/MP4'):
					os.mkdir(output_path+'/MP4')					
				lst_name = lst_file.split('/')[-1].strip('.txt')		
				mxf_file_name = output_path + 'MXF/' + lst_name + '.MXF'
				mp4_file_name = output_path + 'MP4/' + lst_name + '.mp4'
				print "--> Writing MXF file %s | %s" % (mxf_file_name,strftime("%H:%M:%S | %Y-%m-%d",gmtime()))
				ffmpeg_mxf = make_mxf(lst_file,mxf_file_name)
				shell = subprocess.Popen(ffmpeg_mxf)
				shell.wait()
				print '--> MXF File Written to %s' % mxf_file_name
				print '--> Calculating MP4 bitrate...'
				mxf_duration = get_duration_in_seconds(mxf_file_name)
				make_mp4(mxf_file_name,mp4_file_name,mxf_duration)	
				print '--> MP4 File Written to %s | %s' % (mp4_file_name,strftime("%H:%M:%S | %Y-%m-%d",gmtime()))
				os.remove(lst_file)
		return True
	else:
		print "INFO: Found No MXF Files => %s"%path
		return False


def main():
	global OUTPUT_DIRECTORY
	card_folders = sorted([ROOT+'/'+f for f in os.listdir(ROOT) if os.path.isdir(ROOT+'/'+f)])
	for i in card_folders:
		if not os.path.exists(OUTPUT_DIRECTORY + i.split('/')[-1] + '/.komplete'):
			print OUTPUT_DIRECTORY + i.split('/')[-1]
			success = process_folder(i)
			# write hidden file when process is complete
			if success == True:
				completed = file(OUTPUT_DIRECTORY + i.split('/')[-1] + '/.komplete',"w")
				completed.write("True @ %s" % strftime("%H:%M:%S | %Y-%m-%d",gmtime()))
				completed.close()
		else:
			print "INFO: %s has been processed already" % i.split('/')[-1]

event_count = 0

ROOT = "/Volumes/ITMADATA/VIDEO/ITMA video field recordings/in process"
write_disks = ["/Volumes/ITMAVideoDrobo/"]
write_disk_index = 0
OUTPUT_DIRECTORY = write_disks[write_disk_index]
time_limit = None

# cut_off_date = "25/12/2014"
cut_off_date = None

if __name__ == '__main__':
	main()
	print 'Total events %s' % event_count
