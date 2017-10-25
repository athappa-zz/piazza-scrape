import datetime
import scipy.cluster.vq
import numpy as np
import sys


def find_dates(input_filename, events):
	"""
	Takes an input file of piazza posts with timestamps, and the total number of assignments + exams in the course.
	Creates one new file for each event, called event_<num>.txt, containing the timestamp of the event and the Piazza
	posts that correspond to that event.
	"""
	# Get post timestamps in datetime format
	posts = {}
	date_format = "%Y-%m-%dT%H:%M:%SZ"
	starting_date = 0  # Timestamp of the first post in the class
	with open(input_filename, 'r') as input_file:
		count = 1
		post_timestamp = 0
		for line in input_file:
			try:
				post_timestamp = datetime.datetime.strptime(line.strip().split('@@@')[3], date_format)
				posts[post_timestamp] = ''
				if count == 1:
					starting_date = post_timestamp
				else:
					posts[post_timestamp] = line.strip()
				count += 1
			except:
				pass

	# Get cluster division points
	dates = posts.keys()

	# Convert timestamps to ints (seconds since the first post in the class)
	deltas = [(date - starting_date).total_seconds() for date in dates]
	delts = np.array(deltas)
	kmeans = scipy.cluster.vq.kmeans2(delts, events)
	cluster_dict = dict(zip(dates, kmeans[1]))

	# Write each cluster centroid timestamp to file
	for i in range(len(kmeans[0])):
		centroid = starting_date + datetime.timedelta(0, kmeans[0][i])
		with open('event_' + str(i) + '.txt', 'w') as cluster_file:
			cluster_file.write(str(centroid) + '\n')

	# Split up posts and write to file
	cluster_sizes = [0] * events
	for date, post in posts.iteritems():
		cluster_num = cluster_dict[date]
		cluster_sizes[cluster_num] += 1
		with open('event_' + str(cluster_num) + '.txt', 'a') as cluster_file:
			cluster_file.write(post + '\n')

	print('Cluster size date, number of posts:')
	date_dict = {v: k for k, v in cluster_dict.iteritems()}
	for i in range(events):
		print('\t' + 'event_' + str(i) + ': ' + str(date_dict[i]).split()[0] + ', ' + str(cluster_sizes[i]))
	print
	return

if __name__ == '__main__':
	if len(sys.argv) < 3:
		print('Usage: python date_cluster.py <input_filename> <num_events>')
		exit(1)
	find_dates(sys.argv[1], int(sys.argv[2]))