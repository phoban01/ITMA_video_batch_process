import os,subprocess,sys,time,logging,re
from datetime import datetime
from time import gmtime,strftime



def make_mp4(mxf_file_name,mp4_file_name,mxf_duration):
	global time_limit
	# 8192kb = 1MB
	# 1000MB = 1GB
	ideal_file_size = 4499 * 8192
	audio_bit_rate = 320
	# audio bit rate times two because audio is stereo
	video_bitrate = int((ideal_file_size / mxf_duration) - (audio_bit_rate))
	print video_bitrate
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

def humansize(nbytes):
	suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']	
	if nbytes == 0: 
		return '0 B'
	else:
		i = 0
		while nbytes >= 1024 and i < len(suffixes)-1:
			nbytes /= 1024.
			i += 1
		f = ('%.2f' % nbytes).rstrip('0').rstrip('.')
		return '%s %s' % (f, suffixes[i])

def get_file_size(path):
    st = os.path.getsize(path)
    return humansize(st)


def get_duration_in_seconds(mxf_file):
	duration = float(subprocess.check_output(["ffprobe","-v","quiet","-print_format","compact=print_section=0:nokey=1:escape=csv","-show_entries","format=duration",mxf_file]))
	return duration

def main():
	global OUTPUT_DIRECTORY,event_count
	card_folders = sorted([ROOT+'/'+f for f in os.listdir(ROOT) if os.path.isdir(ROOT+'/'+f) and not f.startswith('.')])
	for i in card_folders:
		for root,directory,paths in os.walk(i):
			for path in paths:
				if path.endswith('.mp4'):
					fullpath = os.path.join(root,path)
					size = get_file_size(fullpath)
					if float(size.split()[0]) >= 4.675 and size.split()[-1] == 'GB':
						event_count += 1
						print '--> Shrinking MP4 file %s' % path
						mxf_path = fullpath.replace('MP4','MXF').replace('.mp4','.mxf')
						print '--> Calculating MP4 bitrate...'
						mxf_duration = get_duration_in_seconds(mxf_path)
						# print mxf_duration
						make_mp4(mxf_path,fullpath,mxf_duration)	
						print '--> Shrunken MP4 File Written to %s | %s' % (fullpath,strftime("%H:%M:%S | %Y-%m-%d",gmtime()))

event_count = 0

ROOT = "/Volumes/ITMAVideoDrobo"
write_disks = ["/Volumes/ITMAVideoDrobo/"]
write_disk_index = 0
OUTPUT_DIRECTORY = write_disks[write_disk_index]
time_limit = None

if __name__ == '__main__':
	main()
	print 'Total events %s' % event_count






