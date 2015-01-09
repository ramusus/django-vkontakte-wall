# -*- coding: utf-8 -*-
from django.db import models
from south.db import db
from south.utils import datetime_utils as datetime
from south.v2 import SchemaMigration


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting model 'Comment'
        db.delete_table(u'vkontakte_wall_comment')

        # Removing M2M table for field like_users on 'Comment'
        db.delete_table(db.shorten_name(u'vkontakte_wall_comment_like_users'))

        # Deleting field 'Post.likes'
        db.delete_column(u'vkontakte_wall_post', 'likes')

        # Deleting field 'Post.comments'
        db.delete_column(u'vkontakte_wall_post', 'comments')

        # Deleting field 'Post.wall_owner_content_type'
        db.delete_column(u'vkontakte_wall_post', 'wall_owner_content_type_id')

        # Deleting field 'Post.wall_owner_id'
        db.delete_column(u'vkontakte_wall_post', 'wall_owner_id')

        # Deleting field 'Post.reposts'
        db.delete_column(u'vkontakte_wall_post', 'reposts')

        # Adding field 'Post.owner_content_type'
        db.add_column(u'vkontakte_wall_post', 'owner_content_type',
                      self.gf('django.db.models.fields.related.ForeignKey')(
                          related_name=u'content_type_owners_vkontakte_wall_posts', null=True, to=orm['contenttypes.ContentType']),
                      keep_default=False)

        # Adding field 'Post.owner_id'
        db.add_column(u'vkontakte_wall_post', 'owner_id',
                      self.gf('django.db.models.fields.BigIntegerField')(null=True, db_index=True),
                      keep_default=False)

        # Adding field 'Post.likes_count'
        db.add_column(u'vkontakte_wall_post', 'likes_count',
                      self.gf('django.db.models.fields.PositiveIntegerField')(null=True, db_index=True),
                      keep_default=False)

        # Adding field 'Post.comments_count'
        db.add_column(u'vkontakte_wall_post', 'comments_count',
                      self.gf('django.db.models.fields.PositiveIntegerField')(null=True),
                      keep_default=False)

        # Adding field 'Post.reposts_count'
        db.add_column(u'vkontakte_wall_post', 'reposts_count',
                      self.gf('django.db.models.fields.PositiveIntegerField')(null=True, db_index=True),
                      keep_default=False)

        # Removing M2M table for field repost_users on 'Post'
        db.delete_table(db.shorten_name(u'vkontakte_wall_post_repost_users'))

        # Removing M2M table for field like_users on 'Post'
        db.delete_table(db.shorten_name(u'vkontakte_wall_post_like_users'))

        # Adding M2M table for field likes_users on 'Post'
        m2m_table_name = db.shorten_name(u'vkontakte_wall_post_likes_users')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('post', models.ForeignKey(orm[u'vkontakte_wall.post'], null=False)),
            ('user', models.ForeignKey(orm[u'vkontakte_users.user'], null=False))
        ))
        db.create_unique(m2m_table_name, ['post_id', 'user_id'])

        # Adding M2M table for field reposts_users on 'Post'
        m2m_table_name = db.shorten_name(u'vkontakte_wall_post_reposts_users')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('post', models.ForeignKey(orm[u'vkontakte_wall.post'], null=False)),
            ('user', models.ForeignKey(orm[u'vkontakte_users.user'], null=False))
        ))
        db.create_unique(m2m_table_name, ['post_id', 'user_id'])

        # Changing field 'Post.remote_id'
        db.alter_column(u'vkontakte_wall_post', 'remote_id', self.gf(
            'django.db.models.fields.CharField')(unique=True, max_length=20))

        # Changing field 'Post.author_content_type'
        db.alter_column(u'vkontakte_wall_post', 'author_content_type_id', self.gf(
            'django.db.models.fields.related.ForeignKey')(null=True, to=orm['contenttypes.ContentType']))

        # Changing field 'Post.author_id'
        db.alter_column(u'vkontakte_wall_post', 'author_id', self.gf(
            'django.db.models.fields.BigIntegerField')(null=True))

    def backwards(self, orm):
        # Adding model 'Comment'
        db.create_table(u'vkontakte_wall_comment', (
            ('archived', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('remote_id', self.gf('django.db.models.fields.CharField')(max_length='20', unique=True)),
            ('fetched', self.gf('django.db.models.fields.DateTimeField')(blank=True, null=True, db_index=True)),
            ('raw_html', self.gf('django.db.models.fields.TextField')()),
            ('post', self.gf('django.db.models.fields.related.ForeignKey')
             (related_name='wall_comments', to=orm['vkontakte_wall.Post'])),
            ('text', self.gf('django.db.models.fields.TextField')()),
            ('raw_json', self.gf('annoying.fields.JSONField')(default={}, null=True)),
            ('author_content_type', self.gf('django.db.models.fields.related.ForeignKey')
             (related_name='comments', to=orm['contenttypes.ContentType'])),
            ('wall_owner_id', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            ('reply_for_id', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, db_index=True)),
            ('reply_to', self.gf('django.db.models.fields.related.ForeignKey')
             (to=orm['vkontakte_wall.Comment'], null=True)),
            ('wall_owner_content_type', self.gf('django.db.models.fields.related.ForeignKey')
             (related_name='vkontakte_wall_comments', to=orm['contenttypes.ContentType'])),
            ('likes', self.gf('django.db.models.fields.PositiveIntegerField')(default=0, db_index=True)),
            ('reply_for_content_type', self.gf('django.db.models.fields.related.ForeignKey')
             (related_name='replies', null=True, to=orm['contenttypes.ContentType'])),
            ('date', self.gf('django.db.models.fields.DateTimeField')(db_index=True)),
            ('author_id', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('from_id', self.gf('django.db.models.fields.IntegerField')(null=True)),
        ))
        db.send_create_signal(u'vkontakte_wall', ['Comment'])

        # Adding M2M table for field like_users on 'Comment'
        m2m_table_name = db.shorten_name(u'vkontakte_wall_comment_like_users')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('comment', models.ForeignKey(orm[u'vkontakte_wall.comment'], null=False)),
            ('user', models.ForeignKey(orm[u'vkontakte_users.user'], null=False))
        ))
        db.create_unique(m2m_table_name, ['comment_id', 'user_id'])

        # Adding field 'Post.likes'
        db.add_column(u'vkontakte_wall_post', 'likes',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=0, db_index=True),
                      keep_default=False)

        # Adding field 'Post.comments'
        db.add_column(u'vkontakte_wall_post', 'comments',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=0, db_index=True),
                      keep_default=False)

        # User chose to not deal with backwards NULL issues for 'Post.wall_owner_content_type'
        raise RuntimeError(
            "Cannot reverse this migration. 'Post.wall_owner_content_type' and its values cannot be restored.")

        # The following code is provided here to aid in writing a correct
        # migration        # Adding field 'Post.wall_owner_content_type'
        db.add_column(u'vkontakte_wall_post', 'wall_owner_content_type',
                      self.gf('django.db.models.fields.related.ForeignKey')(
                          related_name='vkontakte_wall_posts', to=orm['contenttypes.ContentType']),
                      keep_default=False)

        # User chose to not deal with backwards NULL issues for 'Post.wall_owner_id'
        raise RuntimeError("Cannot reverse this migration. 'Post.wall_owner_id' and its values cannot be restored.")

        # The following code is provided here to aid in writing a correct
        # migration        # Adding field 'Post.wall_owner_id'
        db.add_column(u'vkontakte_wall_post', 'wall_owner_id',
                      self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True),
                      keep_default=False)

        # Adding field 'Post.reposts'
        db.add_column(u'vkontakte_wall_post', 'reposts',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=0, db_index=True),
                      keep_default=False)

        # Deleting field 'Post.owner_content_type'
        db.delete_column(u'vkontakte_wall_post', 'owner_content_type_id')

        # Deleting field 'Post.owner_id'
        db.delete_column(u'vkontakte_wall_post', 'owner_id')

        # Deleting field 'Post.likes_count'
        db.delete_column(u'vkontakte_wall_post', 'likes_count')

        # Deleting field 'Post.comments_count'
        db.delete_column(u'vkontakte_wall_post', 'comments_count')

        # Deleting field 'Post.reposts_count'
        db.delete_column(u'vkontakte_wall_post', 'reposts_count')

        # Adding M2M table for field repost_users on 'Post'
        m2m_table_name = db.shorten_name(u'vkontakte_wall_post_repost_users')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('post', models.ForeignKey(orm[u'vkontakte_wall.post'], null=False)),
            ('user', models.ForeignKey(orm[u'vkontakte_users.user'], null=False))
        ))
        db.create_unique(m2m_table_name, ['post_id', 'user_id'])

        # Adding M2M table for field like_users on 'Post'
        m2m_table_name = db.shorten_name(u'vkontakte_wall_post_like_users')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('post', models.ForeignKey(orm[u'vkontakte_wall.post'], null=False)),
            ('user', models.ForeignKey(orm[u'vkontakte_users.user'], null=False))
        ))
        db.create_unique(m2m_table_name, ['post_id', 'user_id'])

        # Removing M2M table for field likes_users on 'Post'
        db.delete_table(db.shorten_name(u'vkontakte_wall_post_likes_users'))

        # Removing M2M table for field reposts_users on 'Post'
        db.delete_table(db.shorten_name(u'vkontakte_wall_post_reposts_users'))

        # Changing field 'Post.remote_id'
        db.alter_column(u'vkontakte_wall_post', 'remote_id', self.gf(
            'django.db.models.fields.CharField')(max_length='20', unique=True))

        # User chose to not deal with backwards NULL issues for 'Post.author_content_type'
        raise RuntimeError(
            "Cannot reverse this migration. 'Post.author_content_type' and its values cannot be restored.")

        # The following code is provided here to aid in writing a correct migration
        # Changing field 'Post.author_content_type'
        db.alter_column(u'vkontakte_wall_post', 'author_content_type_id', self.gf(
            'django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType']))

        # User chose to not deal with backwards NULL issues for 'Post.author_id'
        raise RuntimeError("Cannot reverse this migration. 'Post.author_id' and its values cannot be restored.")

        # The following code is provided here to aid in writing a correct migration
        # Changing field 'Post.author_id'
        db.alter_column(u'vkontakte_wall_post', 'author_id', self.gf('django.db.models.fields.PositiveIntegerField')())

    models = {
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'vkontakte_comments.comment': {
            'Meta': {'object_name': 'Comment'},
            'archived': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'author_content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'content_type_authors_vkontakte_comments_comments'", 'null': 'True', 'to': u"orm['contenttypes.ContentType']"}),
            'author_id': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'db_index': 'True'}),
            'date': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'fetched': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'likes_count': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'db_index': 'True'}),
            'likes_users': ('m2m_history.fields.ManyToManyHistoryField', [], {'related_name': "'like_comments'", 'symmetrical': 'False', 'to': u"orm['vkontakte_users.User']"}),
            'object_content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'content_type_objects_vkontakte_comments'", 'to': u"orm['contenttypes.ContentType']"}),
            'object_id': ('django.db.models.fields.BigIntegerField', [], {'db_index': 'True'}),
            'owner_content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'content_type_owners_vkontakte_comments_comments'", 'null': 'True', 'to': u"orm['contenttypes.ContentType']"}),
            'owner_id': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'db_index': 'True'}),
            'remote_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'}),
            'reply_for_content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'replies'", 'null': 'True', 'to': u"orm['contenttypes.ContentType']"}),
            'reply_for_id': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'db_index': 'True'}),
            'reply_to': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['vkontakte_comments.Comment']", 'null': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {})
        },
        u'vkontakte_places.city': {
            'Meta': {'object_name': 'City'},
            'area': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'country': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'cities'", 'null': 'True', 'to': u"orm['vkontakte_places.Country']"}),
            'fetched': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'region': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'remote_id': ('django.db.models.fields.BigIntegerField', [], {'unique': 'True'})
        },
        u'vkontakte_places.country': {
            'Meta': {'object_name': 'Country'},
            'fetched': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'remote_id': ('django.db.models.fields.BigIntegerField', [], {'unique': 'True'})
        },
        u'vkontakte_users.user': {
            'Meta': {'object_name': 'User'},
            'about': ('django.db.models.fields.TextField', [], {}),
            'activity': ('django.db.models.fields.TextField', [], {}),
            'albums': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'audios': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'bdate': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'books': ('django.db.models.fields.TextField', [], {}),
            'city': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['vkontakte_places.City']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            'counters_updated': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['vkontakte_places.Country']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            'facebook': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'facebook_name': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'faculty': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'faculty_name': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'fetched': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'followers': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'friends': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'friends_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'friends_users': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'followers_users'", 'symmetrical': 'False', 'to': u"orm['vkontakte_users.User']"}),
            'games': ('django.db.models.fields.TextField', [], {}),
            'graduation': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'has_avatar': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'has_mobile': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'home_phone': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'interests': ('django.db.models.fields.TextField', [], {}),
            'is_deactivated': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'livejournal': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'mobile_phone': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'movies': ('django.db.models.fields.TextField', [], {}),
            'mutual_friends': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'notes': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'photo': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'photo_big': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'photo_medium': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'photo_medium_rec': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'photo_rec': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'rate': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'relation': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True'}),
            'remote_id': ('django.db.models.fields.BigIntegerField', [], {'primary_key': 'True'}),
            'screen_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'sex': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'skype': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'subscriptions': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'sum_counters': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'timezone': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'tv': ('django.db.models.fields.TextField', [], {}),
            'twitter': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'university': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'university_name': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'user_photos': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'user_videos': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'videos': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'wall_comments': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'})
        },
        u'vkontakte_wall.post': {
            'Meta': {'object_name': 'Post'},
            'archived': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'attachments': ('django.db.models.fields.TextField', [], {}),
            'author_content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'content_type_authors_vkontakte_wall_posts'", 'null': 'True', 'to': u"orm['contenttypes.ContentType']"}),
            'author_id': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'db_index': 'True'}),
            'comments_count': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'copy_owner_content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'vkontakte_wall_copy_posts'", 'null': 'True', 'to': u"orm['contenttypes.ContentType']"}),
            'copy_owner_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'db_index': 'True'}),
            'copy_post': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'wall_reposts'", 'null': 'True', 'to': u"orm['vkontakte_wall.Post']"}),
            'copy_text': ('django.db.models.fields.TextField', [], {}),
            'date': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'fetched': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'geo': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'likes_count': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'db_index': 'True'}),
            'likes_users': ('m2m_history.fields.ManyToManyHistoryField', [], {'related_name': "'like_posts'", 'symmetrical': 'False', 'to': u"orm['vkontakte_users.User']"}),
            'media': ('django.db.models.fields.TextField', [], {}),
            'online': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'}),
            'owner_content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'content_type_owners_vkontakte_wall_posts'", 'null': 'True', 'to': u"orm['contenttypes.ContentType']"}),
            'owner_id': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'db_index': 'True'}),
            'post_source': ('django.db.models.fields.TextField', [], {}),
            'raw_html': ('django.db.models.fields.TextField', [], {}),
            'raw_json': ('annoying.fields.JSONField', [], {'default': '{}', 'null': 'True'}),
            'remote_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'}),
            'reply_count': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'reposts_count': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'db_index': 'True'}),
            'reposts_users': ('m2m_history.fields.ManyToManyHistoryField', [], {'related_name': "'reposts_posts'", 'symmetrical': 'False', 'to': u"orm['vkontakte_users.User']"}),
            'signer_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {})
        }
    }

    complete_apps = ['vkontakte_wall']
