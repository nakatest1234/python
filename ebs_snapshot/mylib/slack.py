#! /usr/bin/env python
# -*- coding: utf-8 -*-


import os
import sys
import datetime

from urlparse import urljoin
from urllib import urlencode
import pprint
import urllib2
import json

# 日本時間
class JST(datetime.tzinfo):
	# UTCからの時間のずれ
	def utcoffset(self, dt):
		return datetime.timedelta(hours=9)

	# サマータイム
	def dst(self, dt): 
		return datetime.timedelta(0)

	# タイムゾーンの名前
	def tzname(self, dt):
		return 'JST'

def slack(url, channel, text, opt=None):
	"""
	SlackにメッセージをPOSTする
	"""
	msg = {"channel":channel,"text":text}

	if opt is not None:
		msg.update(opt)

	if (url):
		payload_json = json.dumps(msg)
		data = urlencode({"payload": payload_json})

		req = urllib2.Request(url)

		#response = urllib2.build_opener(urllib2.HTTPHandler()).open(req, data.encode('utf-8')).read()
		#return response.decode('utf-8')
		urllib2.build_opener(urllib2.HTTPHandler()).open(req, data.encode('utf-8'))
	else:
		print msg


def main():
	event_json = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'slack.json')

	f = open(event_json, 'r')
	if (f):
		data = json.load(f)
		f.close()

		msg = json.dumps(data)
		data['msg'] = '```' + msg + '```'

		slack_post(data['url'], data['channel'], data['msg'], data['opt']);


def lambda_handler(event, context):
	main()


if __name__ == '__main__':

	try:
		main()
	except NameError, e:
		print >> sys.stderr, "NameError:", e.args[0]
	except Exception, e:
		print >> sys.stderr, "Exception:", e.args[0], e.args[1]
	except:
		print >> sys.stderr, "Unexpected error:", sys.exc_info()[0]

