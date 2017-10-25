from __future__ import division
from gensim import corpora, models
from sklearn.metrics import accuracy_score, v_measure_score
from collections import Counter

import numpy as np
import nltk
from nltk.corpus import stopwords
import os
import fnmatch
import re

NUM_EXAMS = 2
EXAM_TAG = 'exam'
PROJ_TAG = 'hw'
STOPWORDS = nltk.corpus.stopwords.words('english')

def get_lines(fname):
	"""Return lines read from given filename"""
	with open(fname, 'r') as infile:
		return infile.readlines()


def tokenize(text):
	"""
	Tokenize text using NLTK's tokenize function
	Discard tokens that have no alphanumeric characters
	"""
	tokens = [word.lower() for sent in nltk.sent_tokenize(text) for word in nltk.word_tokenize(sent)]
	tokens[:] = [token for token in tokens if re.search('[a-zA-Z]', token) != None and len(token) > 3]
	return tokens


def get_docs(lines):
	"""
	Create documents by appending title, question, and answer of each post
	Return all documents in list format
	"""
	docs = []
	labels = []
	date = lines[0]
	for line in lines[1:]:  # First line of file is the date
		parts = line.split('@@@')
		doc_text = ' '.join(parts[:3])  # Space-separated string of <title> <question> <answer>
		docs.append(doc_text)

		# Ignore posts that are neither projects nor exams
		tags = parts[-1].split()
		for tag in tags:
			if tag.find(PROJ_TAG) > -1:
				labels.append(tag)
			elif tag.find(EXAM_TAG) > -1:
				labels.append(EXAM_TAG)
	return date, labels, docs


def run_lda(docs):
	"""
	Tokenize all docs before building dictionary and corpus
	Run LDA with single topic on all documents
	Return average probability of all 10 LDA keywords
	"""
	tokenized_text = [tokenize(text) for text in docs]
	texts = [[word for word in text if word not in STOPWORDS] for text in tokenized_text]
	dictionary = corpora.Dictionary(texts)
	dictionary.filter_extremes(no_below=0.2, no_above=0.75)
	corpus = [dictionary.doc2bow(text) for text in texts]
	lda = models.LdaModel(corpus, num_topics=1, id2word=dictionary, update_every=5, passes=20)

	# Classifying whether a cluster is an exam vs. project
	# Assumes that the lower the probability, the more likely it is that it's a exam
	probs = dict((lda.print_topics(num_topics = 1, num_words=10)))
	topics = ' '.join(re.findall('[a-zA-Z]+', probs[0]))
	print(topics)
	probs[0] = probs[0].replace('*', " ")
	avg = 0
	count = 0
	for prob in probs[0].split():
		if prob.startswith("0"):
			avg += float(prob)
			count += 1
	return avg / count


def process_events():
	"""
	Run LDA topic modeling, with a single topic, on each event
	Return event average LDA word probabilities, dates, total number of posts, and true labels
	"""
	dates = []
	averages = []
	labels_true = {}  # {event_num: list of true labels}
	event_num = 0
	num_posts = 0  # Number of posts that are either exams or projects
	for file in os.listdir('.'):
		if fnmatch.fnmatch(file, 'event_*.txt'):
			print '\tevent_' + str(event_num) + ':',
			lines = [l for l in get_lines(file)]
			date, labels, docs = get_docs(lines)
			dates.append(date)
			labels_true[event_num] = labels
			averages.append(run_lda(docs))

			num_posts += len(labels)
			event_num += 1
	return averages, dates, num_posts, labels_true


def eval_performance(averages, dates, num_posts, labels_true):
	"""
	Predict labels for each cluster based on average probability from LDA model
	Calculate per-event (cluster) accuracy
	Return weighted average of cluster accuracy and V-measure score
	"""
	# Exam event numbers, sorted by increasing probability
	exam_indices = [averages.index(x) for x in sorted(averages)][:NUM_EXAMS]

	# Project event numbers, sorted by increasing date
	proj_indices = [dates.index(x) for x in sorted(dates) if dates.index(x) not in exam_indices]

	labels_pred = {}  # {event_num: list of predicted labels}
	weighted_avg = 0
	for i in range(len(averages)):
		# Build predicted labels based on classification of event
		num_posts_cur = len(labels_true[i])
		is_exam = i in exam_indices
		labels_pred[i] = [EXAM_TAG if is_exam else PROJ_TAG + str(proj_indices.index(i) + 1)] * num_posts_cur

		# Calculate per-event accuracy
		accuracy = accuracy_score(labels_true[i], labels_pred[i])
		weighted_avg += (num_posts_cur / num_posts) * accuracy

		# Emit the event classification and its accuracy
		print '\tevent_' + str(i) + ':',
		print labels_pred[i][0] + ', (' + Counter(labels_true[i]).most_common(1)[0][0] + '),',
		print accuracy

	# Calculate V-measure score for concatenated labels of all event clusters
	labels_pred_list = []
	labels_true_list = []
	for i in range(len(averages)):
		labels_pred_list.extend(labels_pred[i])
		labels_true_list.extend(labels_true[i])
	v_measure = v_measure_score(labels_true_list, labels_pred_list)

	return weighted_avg, v_measure


def main():
	print('Top-10 LDA keywords:')
	averages, dates, num_posts, labels_true = process_events()

	print('\nPredicted label, (most likely true label), accuracy:')
	weighted_avg, v_measure = eval_performance(averages, dates, num_posts, labels_true)

	print('\nOverall accuracy: ' + str(weighted_avg))
	print('\nV-measure score: ' + str(v_measure))

if __name__ == '__main__':
	main()