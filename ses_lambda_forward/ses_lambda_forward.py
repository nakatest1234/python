#! /usr/bin/env python
# -*- coding: utf-8 -*-


import os
import sys
import types
import boto3
from email.mime.text        import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart   import MIMEMultipart
from email.Header           import Header
from email.Utils            import formatdate

import datetime
import json
import inspect
from pprint import pprint
from syslog import syslog


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


def main(event, context):
	syslog(inspect.currentframe().f_code.co_name)
	syslog('===START===')

	config = {
		'ses_region': os.environ.get('SES_REGION',   'us-west-1'),
		'mail_from' : os.environ.get('MAIL_FROM',    ''),
		'mail_to'   : os.environ.get('MAIL_TO',      ''),
		'subject'   : os.environ.get('MAIL_SUBJECT', ''),
	}

	if (len(config['mail_from'])>0 and len(config['mail_to'])>0):
		tmp = s3_download(config, event)

		if (len(tmp)>0):
			email = make_email(config, tmp)

			ses_sendmail(config, email)

			os.remove(tmp)
	else:
		pprint('No from or recept')

	syslog('===END===')
	

def s3_download(config, event):
	syslog(inspect.currentframe().f_code.co_name)

	bucket = ''
	key    = ''

	if (event.get('Records') and isinstance(event.get('Records'), types.ListType) and event.get('Records')[0].get('s3')):
		event_s3 = event['Records'][0]['s3']

		if (event_s3.get('bucket') and event_s3.get('bucket').get('name')):
			bucket = event_s3['bucket']['name']

		if (event_s3.get('object') and event_s3.get('object').get('key')):
			key = event_s3['object']['key']

	tmp = os.path.join('/tmp', os.path.basename(key)+'.eml')
	syslog(tmp)

	## get S3 file
	s3 = boto3.client('s3')

	try:
		s3.download_file(Bucket=bucket, Key=key, Filename=tmp)

		return tmp
	except Exception as e:
		pprint(e)

	return ''


def make_email(config, tmp, encoding='utf-8'):
	syslog(inspect.currentframe().f_code.co_name)

	msg = MIMEMultipart('mixed')

	msg['Subject'] = Header(config.get('subject', ''), encoding)
	msg['From']    = config.get('mail_from')
	msg['To']      = config.get('mail_to')
	msg['Date']    = formatdate(localtime=True)

	msg.set_charset(encoding)

	msg.preamble = 'This mail is multipart/mixed.\n'

	msg.attach(MIMEText('get mail. To: %s' % config.get('mail_from'), 'plain', encoding))

	with open(tmp, "rb") as f:
		fname = os.path.basename(tmp)

		part = MIMEApplication(f.read(), _subtype='octet-stream', Name=fname)
		part.add_header('Content-Disposition', 'attachment', filename=fname)

		msg.attach(part)

	return msg


def ses_sendmail(config, email):
	syslog(inspect.currentframe().f_code.co_name)

	try:
		client = boto3.client('ses', region_name=config['ses_region'])
		response = client.send_raw_email(
			#Source=config['mail_from'],
			#Destinations=[
			#	config['mail_to'],
			#],
			RawMessage={
				'Data': email.as_string()
			},
		)
	except Exception as e:
		pprint(e)


def lambda_handler(event, context):
	syslog(inspect.currentframe().f_code.co_name)
	main(event, context)

if __name__ == '__main__':

	event = {}

	try:
		main(event, None)
	except NameError, e:
		print >> sys.stderr, "NameError:", e.args[0]
	except Exception, e:
		print >> sys.stderr, "Exception:", e.args[0], e.args[1]
	except:
		print >> sys.stderr, "Unexpected error:", sys.exc_info()[0]

