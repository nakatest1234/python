#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import inspect
import json
import urllib.parse
import re
import boto3

from pprint import pprint


def main(event, context):
	#pprint(os.environ)
	#print(event)

	# 環境変数からパラメータ取得
	search_prefix   = os.environ.get('SEARCH_PRIFIX', '')
	replace_targets = os.environ.get('REPLACE_TARGETS', '').split(',')

	# バケットの情報を取得
	bucket = event['Records'][0]['s3']['bucket']['name']
	key    = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')

	# 環境別のパスを消して相対パスを作成
	path = re.sub('^{}'.format(search_prefix), '', key)

	try:
		s3 = boto3.resource('s3')

		for target in replace_targets:
			target_bucket, target_subdir = target.split('/', 2)
			target_path = '{}/{}'.format(target_subdir, path)

			print('{}/{} -> {}/{}'.format(bucket,key, target_bucket,target_path))
			s3.Object(target_bucket, target_path).copy_from(CopySource={'Bucket':bucket,'Key':key})

	except Exception as e:
		print(e)
		print('Error getting object {} from bucket {}. Make sure they exist and your bucket is in the same region as this function.'.format(key, bucket))
		raise e


def lambda_handler(event, context):
	#print(inspect.currentframe().f_code.co_name)
	main(event, context)


if __name__ == '__main__':
	event = {}

	try:
		main(event, None)
	except NameError as e:
		print("NameError:", e.args[0], file=sys.stderr)
	except Exception as e:
		print("Exception:", e.args[0], e.args[1], file=sys.stderr)
	except:
		print("Unexpected error:", sys.exc_info()[0], file=sys.stderr)
