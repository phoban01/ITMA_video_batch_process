# this script takes a list of mxf files, concatenates them 
# and outputs an mp4 file at 1080p
import os,subprocess,sys,time,logging
from datetime import datetime
from time import gmtime,strftime

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
		if write_disk_index == 0:
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


def time_group(lst,limit=1):
	'''Limit is time limit in hours between separate events'''
	groups = []
	g = [lst[0]]
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
	groups.append(g)
	for i,j in enumerate(groups):
		start = creation_time(j[0])
		end = creation_time(j[-1])
		delta = datetime.strptime(end['full'],end['FMT']) - datetime.strptime(start['full'],start['FMT'])
	return groups

def get_mxf_files(path):
	mxfers = []
	for r,d,f in os.walk(path):
		for fx in f:
			if fx.endswith('.MXF'):
				mxfers.append(r+'/'+fx)
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
		fl_path = output_path + event_name.replace(' ','_') + "_event_%s.txt" % (i+1)
		paths.append(fl_path)
		event_file_list = open(fl_path,"w")
		for i in event:
			event_file_list.write("file %s\n" % i.replace(' ','\ '))
		event_file_list.close()
	return paths

def write_metadata_file(event_name,output_path,items,path,names):
	data_file = open(output_path+"folder_metadata.txt","w")
	data_file.write("%%%%% Metadata for folder: {0} %%%%% \n\n".format(event_name))
	data_file.write('SOURCE: %s\n\n'%path)
	data_file.write('ITEMS: %s\n\n'%len(items))
	data_file.write('CREATED ON:\n')
	for i,obj in enumerate(items):
		data_file.write('\tITEM %s: %s %s \n\n'%(i+1,creation_time(obj[0])['date'],creation_time(obj[0])['time']))
	data_file.write("CONTENTS DURATIONS:\n\n")
	for i,obj in enumerate(items):
		data_file.write('\tITEM %s Duration:%s\n'%(i+1,get_duration(obj)))
	data_file.write("THE FOLLOWING NAMES WERE FOUND:\n")
	for i,obj in enumerate(names):
		data_file.write("\t%s: %s\n\n"%(i+1,obj))
	data_file.write("\n%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
	data_file.close()
	return None

def make_mxf(lst_file,mxf_file_name):
	global time_limit
	ffmpeg_cmd = ["ffmpeg", 
				"-n",
				"-f","concat",
				"-i",lst_file,
				"-c","copy",
				"-v","quiet",
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
	ideal_file_size = 4500 * 8192
	audio_bit_rate = 320
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
				"-b:a",str(audio_bit_rate)+'k',
				"-v","quiet",
				"-f","mp4"
				]
	if time_limit != None:
		ffmpeg_cmd.append("-t")
		ffmpeg_cmd.append(str(time_limit))
	ffmpeg_cmd.append("/dev/null")
	print 'Executing first pass MP4 File %s' % mp4_file_name
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
				"-b:a",str(audio_bit_rate)+'k',				
				"-v","quiet"
				]
	if time_limit != None:
		ffmpeg_cmd.append("-t")
		ffmpeg_cmd.append(str(time_limit))
	ffmpeg_cmd.append(mp4_file_name)
	print 'Executing second pass MP4 File %s' % mp4_file_name	
	shellCmd = subprocess.Popen(ffmpeg_cmd)	
	shellCmd.wait()

def process_folder(path):
	global OUTPUT_DIRECTORY
	event_name = path.split('/')[-1]
	output_path = OUTPUT_DIRECTORY + event_name + '/'
	mxf_files = get_mxf_files(path) 
	mxf_files.sort(key=lambda x:creation_time(x))
	if len(mxf_files) > 0:
		items = time_group(mxf_files)
		names = get_names(path)
		if not os.path.exists(output_path):
			os.mkdir(output_path)
		print "Writing Metadata for %s" % event_name 
		write_metadata_file(event_name,output_path,items,path,names)	
		print "Metadata Written"
		paths = write_file_lists(items,output_path,event_name)
		for lst_file in paths:
			# check if enough disk-space is left : returns True if a switch has occured.
			if check_disk_usage(0.925) == True:
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
			print "Write MXF file %s" % mxf_file_name
			ffmpeg_mxf = make_mxf(lst_file,mxf_file_name)
			shell = subprocess.Popen(ffmpeg_mxf)
			shell.wait()
			print 'MXF File Written to %s' % mxf_file_name
			print 'Calculating MP4 bitrate...'
			mxf_duration = get_duration_in_seconds(mxf_file_name)
			make_mp4(mxf_file_name,mp4_file_name,mxf_duration)	
			print 'MP4 File Write to %s' % mp4_file_name
			os.remove(lst_file)
	else:
		print "Found No MXF Files => %s"%path


def main():
	card_folders = [ROOT+'/'+f for f in os.listdir(ROOT) if os.path.isdir(ROOT+'/'+f)]
	for i in card_folders[0:3]:
		process_folder(i)

# MIGHT want to add some overwrite protection in case repeat runs are needed.

ROOT = "/Volumes/ITMADATA/VIDEO/ITMA video field recordings/in process"
write_disks = ["/Volumes/Processed Video Field Recordings Disk 1/","/Volumes/Processed Video Field Recordings Disk 2/"]
write_disk_index = 0
OUTPUT_DIRECTORY = write_disks[write_disk_index]
time_limit = 10

if __name__ == '__main__':
	main()
