# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'Comment.reply_to_uid'
        db.delete_column('vkontakte_wall_comment', 'reply_to_uid')

        # Deleting field 'Comment.reply_to_cid'
        db.delete_column('vkontakte_wall_comment', 'reply_to_cid')

        # Adding field 'Comment.reply_for'
        db.add_column('vkontakte_wall_comment', 'reply_for',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['vkontakte_users.User'], null=True),
                      keep_default=False)

        # Adding field 'Comment.reply_to'
        db.add_column('vkontakte_wall_comment', 'reply_to',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['vkontakte_wall.Comment'], null=True),
                      keep_default=False)

        # Adding field 'Post.group'
        db.add_column('vkontakte_wall_post', 'group',
                      self.gf('django.db.models.fields.related.ForeignKey')(related_name='posts', null=True, to=orm['vkontakte_groups.Group']),
                      keep_default=False)

        # Adding M2M table for field like_users on 'Post'
        db.create_table('vkontakte_wall_post_like_users', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('post', models.ForeignKey(orm['vkontakte_wall.post'], null=False)),
            ('user', models.ForeignKey(orm['vkontakte_users.user'], null=False))
        ))
        db.create_unique('vkontakte_wall_post_like_users', ['post_id', 'user_id'])

        # Adding M2M table for field repost_users on 'Post'
        db.create_table('vkontakte_wall_post_repost_users', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('post', models.ForeignKey(orm['vkontakte_wall.post'], null=False)),
            ('user', models.ForeignKey(orm['vkontakte_users.user'], null=False))
        ))
        db.create_unique('vkontakte_wall_post_repost_users', ['post_id', 'user_id'])


        # Changing field 'Post.author'
        db.alter_column('vkontakte_wall_post', 'author_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['vkontakte_users.User']))

        # Changing field 'Post.owner'
        db.alter_column('vkontakte_wall_post', 'owner_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['vkontakte_users.User']))
    def backwards(self, orm):
        # Adding field 'Comment.reply_to_uid'
        db.add_column('vkontakte_wall_comment', 'reply_to_uid',
                      self.gf('django.db.models.fields.IntegerField')(null=True),
                      keep_default=False)

        # Adding field 'Comment.reply_to_cid'
        db.add_column('vkontakte_wall_comment', 'reply_to_cid',
                      self.gf('django.db.models.fields.IntegerField')(null=True),
                      keep_default=False)

        # Deleting field 'Comment.reply_for'
        db.delete_column('vkontakte_wall_comment', 'reply_for_id')

        # Deleting field 'Comment.reply_to'
        db.delete_column('vkontakte_wall_comment', 'reply_to_id')

        # Deleting field 'Post.group'
        db.delete_column('vkontakte_wall_post', 'group_id')

        # Removing M2M table for field like_users on 'Post'
        db.delete_table('vkontakte_wall_post_like_users')

        # Removing M2M table for field repost_users on 'Post'
        db.delete_table('vkontakte_wall_post_repost_users')


        # Changing field 'Post.author'
        db.alter_column('vkontakte_wall_post', 'author_id', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['vkontakte_users.User']))

        # Changing field 'Post.owner'
        db.alter_column('vkontakte_wall_post', 'owner_id', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['vkontakte_users.User']))
    models = {
        'vkontakte_groups.group': {
            'Meta': {'ordering': "['name']", 'object_name': 'Group'},
            'fetched': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_admin': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '800'}),
            'photo': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'photo_big': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'photo_medium': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'remote_id': ('django.db.models.fields.BigIntegerField', [], {'unique': 'True'}),
            'screen_name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['vkontakte_users.User']", 'symmetrical': 'False'})
        },
        'vkontakte_places.city': {
            'Meta': {'ordering': "['name']", 'object_name': 'City'},
            'area': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'country': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'cities'", 'null': 'True', 'to': "orm['vkontakte_places.Country']"}),
            'fetched': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'region': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'remote_id': ('django.db.models.fields.BigIntegerField', [], {'unique': 'True'})
        },
        'vkontakte_places.country': {
            'Meta': {'ordering': "['name']", 'object_name': 'Country'},
            'fetched': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'remote_id': ('django.db.models.fields.BigIntegerField', [], {'unique': 'True'})
        },
        'vkontakte_users.user': {
            'Meta': {'ordering': "['remote_id']", 'object_name': 'User'},
            'activity': ('django.db.models.fields.TextField', [], {}),
            'albums': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'audios': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'bdate': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'city': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['vkontakte_places.City']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            'counters_updated': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['vkontakte_places.Country']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            'faculty': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'faculty_name': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'fetched': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'followers': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'friends': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'graduation': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'has_mobile': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'home_phone': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'mobile_phone': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'mutual_friends': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'notes': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'photo': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'photo_big': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'photo_medium': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'photo_medium_rec': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'photo_rec': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'rate': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'relation': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True'}),
            'remote_id': ('django.db.models.fields.BigIntegerField', [], {'unique': 'True'}),
            'screen_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'sex': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'subscriptions': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'sum_counters': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'timezone': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'university': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'university_name': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'user_photos': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'user_videos': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'videos': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'wall_comments': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'vkontakte_wall.comment': {
            'Meta': {'ordering': "['remote_id']", 'object_name': 'Comment'},
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'fetched': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'from_id': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'likes': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'post': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'wall_comments'", 'to': "orm['vkontakte_wall.Post']"}),
            'remote_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': "'20'"}),
            'reply_for': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['vkontakte_users.User']", 'null': 'True'}),
            'reply_to': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['vkontakte_wall.Comment']", 'null': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'comments'", 'to': "orm['vkontakte_users.User']"})
        },
        'vkontakte_wall.post': {
            'Meta': {'ordering': "['remote_id']", 'object_name': 'Post'},
            'attachments': ('django.db.models.fields.TextField', [], {}),
            'author': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'posts'", 'null': 'True', 'to': "orm['vkontakte_users.User']"}),
            'comments': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'copy_owner_id': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'copy_post_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'copy_text': ('django.db.models.fields.TextField', [], {}),
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'fetched': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'geo': ('django.db.models.fields.TextField', [], {}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'posts'", 'null': 'True', 'to': "orm['vkontakte_groups.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'like_users': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'like_posts'", 'blank': 'True', 'to': "orm['vkontakte_users.User']"}),
            'likes': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'media': ('django.db.models.fields.TextField', [], {}),
            'online': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'wall'", 'null': 'True', 'to': "orm['vkontakte_users.User']"}),
            'post_source': ('django.db.models.fields.TextField', [], {}),
            'remote_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': "'20'"}),
            'reply_count': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'}),
            'repost_users': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'repost_posts'", 'blank': 'True', 'to': "orm['vkontakte_users.User']"}),
            'reposts': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'signer_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {})
        }
    }

    complete_apps = ['vkontakte_wall']