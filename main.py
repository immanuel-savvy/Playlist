import os
from re import sub
from sys import argv
from random import shuffle
from time import time

AUDIOS = '.mp3'
VIDEOS = '.mp4'
home = os.environ['HOME']

# -s  search_string "kygo-marshmallow" kygo marshmallow
# -c  use cvlc
# -a  audio only
# -v  video only
# -d  base_directory
# -m  max_directory_search_depth
# -ss double search term
# -n  number of matches / "all" if not specified
# -rn random match count


search_list = list()
base_path = str()
audio_only = None
video_only = None
cvlc = None
no_of_matches = 0
random_matches = 0
max_depth = 10

_playlist_folder_path = home+'/.playlist_folder'
_default_playlist_folders = "Music\nVideos\nDesktop\nDownloads"

# To speed thing up
# Set up a .playlist_folder in your home directory
# format:
# Music
# Desktop
# Downloads

directories = ""

# Functions
def treat_directories():
	global directories
	try:
		read_dir = open(_playlist_folder_path, "r")
		directories = read_dir.read()
		read_dir.close()
	except FileNotFoundError:
		write_dirs = open(_playlist_folder_path, 'w')
		write_dirs.write(_default_playlist_folders)
		write_dirs.close()
		directories = _default_playlist_folders
	directories = [x for x in directories.split('\n') if x]

def treat_command_line_argv():
	global video_only, audio_only, search_list, base_path, max_depth, \
		cvlc, double_search_list, no_of_matches, random_matches
	parameters = ['-s','-a','-c','-v','-d','-m', '-n', '-rn']
	argd = dict()
	args = argv[1:]
	for p in parameters:
		argd.setdefault(p, False)
	current_parameter = args[0]
	for arg in args:
		try:
			parameters.index(arg)
			current_parameter = arg
			argd[current_parameter] = list()
		except ValueError:
			argd[current_parameter].append(arg)

	video_only = type(argd['-v']) == list
	audio_only = type(argd['-a']) == list
	cvlc = type(argd['-c']) == list
	search_list = argd['-s']
	base_path = (argd['-d'] or [os.environ['HOME']])[0]
	try:
		no_of_matches = int(argd['-n'][0])
	except (ValueError, TypeError):
		no_of_matches = 0
	try:
		random_matches = int(argd['-rn'][0])
	except (ValueError, TypeError):
		random_matches = 0
	try:
		max_depth = int(argd['-m'][0])
	except (ValueError, TypeError):
		max_depth = max_depth


def test_path_oserror(path):
	path_list = path.split('/')[1:]

	if len(path_list) >= 5:
		try:
			if path_list[-5:].count(path_list[-1]) == 5:
				raise OSError
		except IndexError:
			pass

treat_directories()
treat_command_line_argv()

# Scow directories
files = list()
items = list()
def read_directory(path):
	if len(files) and len(files) == no_of_matches:
		return
	if len(path.split('/')) > int(max_depth):
		return
	in_d = False
	for d in directories:
		try:
			path.index(d)
			in_d = True
		except ValueError:
			pass
	if not in_d and path != base_path:
		return

	contents = os.listdir(path)
	next_path = None

	for index in range(len(contents)):
		item = contents[index]
		try:
			if type(item) != str or item.startswith('.'):
				continue

			match_list = list()
			for search_term in search_list:
				match_term = True
				search_term = search_term.split('-')
				itr = 0
				while match_term and itr < len(search_term):
					term = search_term[itr]
					itr = itr + 1
					match_term = True
					try:
						item.lower().index(term)
					except ValueError:
						match_term = False
						try:
							try_path = path+'/%s'%item
							os.listdir(try_path)
							raise ValueError
						except NotADirectoryError:
							pass

				match_list.append(match_term)

			match = False
			for m in match_list:
				if m: match = True

			if match:
				if video_only and not item.endswith(VIDEOS):
					continue
				if audio_only and not item.endswith(AUDIOS):
					continue
				if not item.endswith(AUDIOS) and not item.endswith(VIDEOS):
					raise ValueError
				if not items.count(item):
					if not no_of_matches or len(files) < no_of_matches:
						files.append(path+'/%s'%item)
				items.append(item)
		except ValueError:
			try:
				try_path = path+'/%s'%item
				os.listdir(try_path)
				if index < len(contents) - 1:
					next_path = path+'/%s'%contents[index+1]
				test_path_oserror(path)
				read_directory(try_path)
			except NotADirectoryError:
				pass
			except OSError:
				if not next_path:
					return
				read_directory(next_path)


start_time = time()
read_directory(base_path)
total_time = time() - start_time
print("Time: %s"%(total_time))


# Prepare command
command = '%s -Z -L ' % 'cvlc' if cvlc else 'vlc '
shuffle(files)
for i in range(len(files)):
	if random_matches and random_matches == i:
		break
	file = files[i]
	try:
		file.index("'")
		file = sub("'",'',file)
	except ValueError:
		pass
	command = command + "'%s' "%file
print(command)

# Run command
os.system(command)
