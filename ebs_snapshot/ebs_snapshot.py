#! /usr/bin/env python
# -*- coding: utf-8 -*-

from pprint import pprint
import boto3
import os
import sys
import types
import syslog
import time
import json

DRYRUN_FLG = False

def snapshot(tag):
	date = time.strftime('%Y%m%d-%H%M%S')
	ignore_ss = []

	ec2 = boto3.client('ec2')


	# AMIに使ってるスナップショットはエラーになるので除外するためのリスト
	amis = ec2.describe_images(
		DryRun   = DRYRUN_FLG,
		Owners = ['self'],
	)

	if (isinstance(amis, types.DictType) and amis.has_key('Images')):
		for image in amis['Images']:
			for device in image['BlockDeviceMappings']:
				ignore_ss.append(device['Ebs']['SnapshotId'])


	# 対象タグを持ったボリュームを探す
	volumes = ec2.describe_volumes(
		DryRun  = DRYRUN_FLG,
		Filters = [
			{'Name':'status',  'Values':['available', 'in-use']},
			{'Name':'tag-key', 'Values':[tag]},
		]
	)

	if (isinstance(volumes, types.DictType) and volumes.has_key('Volumes')):
		for volume in volumes['Volumes']:
			list_name = filter(lambda d: d['Key']=='Name', volume['Tags'])
			list_tag =  filter(lambda d: d['Key']==tag, volume['Tags'])

			# volume_id, ネーム, 対象タグの値を取得
			volume_id   = volume['VolumeId']
			volume_name = volume_id if len(list_name)==0 else list_name[0]['Value']
			tag_value   = 0         if len(list_tag) ==0 else int(list_tag[0]['Value'])


			# snapshot作成
			res_create_ss = ec2.create_snapshot(
				DryRun      = DRYRUN_FLG,
				VolumeId    = volume_id,
				Description = '{tag}_{date}'.format(tag=tag, date=date),
			)

			if (isinstance(res_create_ss, types.DictType) and res_create_ss.has_key('SnapshotId')):
				syslog.syslog('create snapshot {volume_name}=>{id}'.format(volume_name=volume_name, id=res_create_ss['SnapshotId']))

				# 作成したスナップショットに名前を付与
				res_add_name = ec2.create_tags(
					DryRun    = DRYRUN_FLG,
					Resources = [res_create_ss['SnapshotId']],
					Tags      = [{'Key':'Name', 'Value':volume_name}],
				)
			else:
				syslog.syslog('Cant create snapshot {volume_name}'.format(volume_name=volume_name))

			# backup数リミットあれば
			if (tag_value>0):
				# sleep
				time.sleep(0.01)

				# ボリューム別のスナップショット一覧
				res_list_ss = ec2.describe_snapshots(
					DryRun   = DRYRUN_FLG,
					OwnerIds = ['self'],
					Filters  = [
						{'Name':'volume-id', 'Values':[volume_id]},
					],
				)

				if (isinstance(res_list_ss, types.DictType) and res_list_ss.has_key('Snapshots')):
					list_del = []
					list_tmp = map(lambda v:v['SnapshotId'], sorted(res_list_ss['Snapshots'], key=lambda v:v['StartTime']))

					for ignore_id in ignore_ss:
						try:
							list_tmp.remove(ignore_id)
						except ValueError:
							pass

					len_tmp = len(list_tmp)

					if (len_tmp>tag_value):
						list_del = list_tmp[0:len_tmp-tag_value]

					# 最新の残す以外の過去データを削除
					if (len(list_del)>0):
						for id in list_del:
							syslog.syslog('delete snapshot {id}'.format(id=id))
							ec2.delete_snapshot(DryRun=DRYRUN_FLG,SnapshotId=id)
	else:
		syslog.syslog('No volumes.')
		return False

	return True


# slackに投げる
def post_slack(data, msg):
	from mylib.slack import slack
	if (isinstance(data, types.DictType) and data.has_key('url') and data.has_key('channel')):
		slack(data['url'], data['channel'], msg, data['opt']);


def lambda_handler(event, context):
	try:
		main()
	except NameError, e:
		print >> sys.stderr, "NameError:", e.args[0]
	except Exception, e:
		print >> sys.stderr, "Exception:", e.args[0], e.args[1]
	except:
		print >> sys.stderr, "Unexpected error:", sys.exc_info()[0]


def main():
	config = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'config.json')

	f = open(config, 'r')
	if (f):
		data = json.load(f)
		f.close()

		# タグ設定確認
		if (isinstance(data, types.DictType) and data.has_key('tag')):
			if (snapshot(data['tag'])):
				# スナップショット成功したら、slack定義あれば投げる
				if (isinstance(data, types.DictType) and data.has_key('slack')):
					post_slack(data['slack'], 'AUTO SNAPSHOT tag={tag}: OK'.format(tag=data['tag']))


if __name__ == '__main__':
	try:
		main()
	except NameError, e:
		print >> sys.stderr, "NameError:", e.args[0]
	except Exception, e:
		print >> sys.stderr, "Exception:", e.args[0], e.args[1]
	except:
		print >> sys.stderr, "Unexpected error:", sys.exc_info()[0]

