#! /usr/bin/env python
# -*- coding: utf-8 -*-

from pprint import pprint
import boto3
import sys
import types
import syslog
import time

dryrun_flg=False

def main(tag):
	date = time.strftime('%Y%m%d-%H%M%S')
	ignore_ss = []

	ec2 = boto3.client('ec2')


	# AMIに使ってるスナップショットはエラーになるので除外するためのリスト
	amis = ec2.describe_images(
		DryRun   = dryrun_flg,
		Owners = ['self'],
	)

	if (isinstance(amis, types.DictType) and amis.has_key('Images')):
		for image in amis['Images']:
			for device in image['BlockDeviceMappings']:
				ignore_ss.append(device['Ebs']['SnapshotId'])


	# 対象タグを持ったボリュームを探す
	volumes = ec2.describe_volumes(
		DryRun  = dryrun_flg,
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
				DryRun      = dryrun_flg,
				VolumeId    = volume_id,
				Description = '{tag}_{date}'.format(tag=tag, date=date),
			)

			if (isinstance(res_create_ss, types.DictType) and res_create_ss.has_key('SnapshotId')):
				syslog.syslog('create snapshot {volume_name}=>{id}'.format(volume_name=volume_name, id=res_create_ss['SnapshotId']))

				# 作成したスナップショットに名前を付与
				res_add_name = ec2.create_tags(
					DryRun    = dryrun_flg,
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
					DryRun   = dryrun_flg,
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
							ec2.delete_snapshot(DryRun=dryrun_flg,SnapshotId=id)
	else:
		syslog.syslog('No volumes.')

	return True


if __name__ == '__main__':

	args = sys.argv

	if (len(args) == 2):
		try:
			# args[1] = TAG
			main(args[1])
		except NameError, e:
			print >> sys.stderr, "NameError:", e.args[0]
		except Exception, e:
			print >> sys.stderr, "Exception:", e.args[0], e.args[1]
		except:
			print >> sys.stderr, "Unexpected error:", sys.exc_info()[0]
	else:
		print u'Usage: {script_name} <TAG_NAME>'.format(script_name=args[0])
		quit()

