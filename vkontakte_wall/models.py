# -*- coding: utf-8 -*-
from django.db import models
from django.dispatch import Signal
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from datetime import datetime
from vkontakte_api.utils import api_call
from vkontakte_api import fields
from vkontakte_api.models import VkontakteManager, VkontakteModel
from vkontakte_api.decorators import fetch_all
from vkontakte_users.models import User
from vkontakte_groups.models import Group
from parser import VkontakteWallParser, VkontakteParseError
import logging
import re

log = logging.getLogger('vkontakte_wall')

parsed = Signal(providing_args=['sender', 'instance', 'container'])

class PostRemoteManager(VkontakteManager):

    @fetch_all(return_all=lambda user,*a,**k: user.wall_posts.all())
    def fetch_user_wall(self, user, offset=0, count=None, filter='all', extended=False, **kwargs):

        if filter not in ['owner','others','all']:
            raise ValueError("Attribute 'fiter' has illegal value '%s'" % filter)
        if count > 100:
            raise ValueError("Attribute 'count' can not be more than 100")

        kwargs['owner_id'] = user.remote_id
        kwargs['filter'] = filter
        kwargs['extended'] = int(extended)
        kwargs['offset'] = int(offset)
        if count:
            kwargs.update({'count': count})

        log.debug('Fetching post of user "%s", offset %d' % (user, offset))

        return self.fetch(**kwargs)

    def fetch_group_wall(self, group, offset=0, count=None, own=False, after=None):
        post_data = {
            'al':1,
            'offset': offset,
            'own': int(own), # posts by only group or any users
            'part': 1, # without header, footer
        }

        log.debug('Fetching post of group "%s", offset %d' % (group, offset))

        parser = VkontakteWallParser().request('/wall-%s' % group.remote_id, data=post_data)

        items = parser.content_bs.findAll('div', {'class': re.compile('^post'), 'id': re.compile('^post-%d' % group.remote_id)})

        current_count = offset + len(items)
        need_cut = count and count < current_count
        if need_cut:
            items = items[:count-offset]

        for item in items:

            try:
                post = parser.parse_post(item, group)
            except VkontakteParseError, e:
                log.error(e)
                continue

            if after and post.date < after:
                need_cut = True
                break

            post.raw_html = unicode(item)
            post.save()
            parsed.send(sender=Post, instance=post, container=item)

        if len(items) == 20 and not need_cut:
            return self.fetch_group_wall(group, offset=current_count, count=count, own=own, after=after)
        elif after and need_cut:
            return group.wall_posts.filter(date__gte=after)
        else:
            return group.wall_posts.all()

class CommentRemoteManager(VkontakteManager):

    @fetch_all(return_all=lambda post,*a,**k: post.wall_comments.all())
    def fetch_user_post(self, post, offset=0, count=None, **kwargs):
        if count > 100:
            raise ValueError("Attribute 'count' can not be more than 100")

        kwargs['owner_id'] = post.wall_owner.remote_id
        kwargs['post_id'] = post.remote_id.split('_')[1]
        kwargs['preview_length'] = 0
        kwargs['sort'] = 'asc'
        kwargs['offset'] = int(offset)

        if count:
            kwargs.update({'count': count})

        kwargs['extra_fields'] = {'post_id': post.id}

        log.debug('Fetching comments to post "%s" of user "%s", offset %d' % (post.remote_id, post.wall_owner, offset))

        return self.fetch(**kwargs)

    def fetch_group_post(self, post, offset=0, count=None):#, after=None, only_new=False):
        post_data = {
            'al':1,
            'offset': offset,
            'part': 1,
        }

        log.debug('Fetching comments to post "%s" of group "%s", offset %d' % (post.remote_id, post.wall_owner, offset))

        parser = VkontakteWallParser().request('/wall%s' % (post.remote_id), data=post_data)

        items = parser.content_bs.findAll('div', {'class': 'fw_reply'})

        current_count = offset + len(items)
        need_cut = count and count < current_count
        if need_cut:
            items = items[:count-offset]

#        # get date of last comment and set after attribute
#        if only_new:
#            comments = post.wall_comments.order_by('-date')
#            if comments:
#                after = comments[0].date

        for item in items:

            try:
                comment = parser.parse_comment(item, post.wall_owner)
            except VkontakteParseError, e:
                log.error(e)
                continue

            comment.post = post
            comment.raw_html = unicode(item)
            comment.save()
            parsed.send(sender=Comment, instance=comment, container=item)

#            if after and comment.date < after:
#                need_cut = True
#                break

        if len(items) == 20 and not need_cut:
            return self.fetch_group_post(post, offset=current_count, count=count)#, after=after, only_new=only_new)
#        elif after and need_cut:
#            return post.wall_comments.filter(date__gte=after)
        else:
            if not count:
                post.comments = post.wall_comments.count()
                post.save()
            return post.wall_comments.all()

class WallAbstractModel(VkontakteModel):
    class Meta:
        abstract = True

    methods_namespace = 'wall'
    slug_prefix ='wall'

    remote_id = models.CharField(u'ID', max_length='20', help_text=u'Уникальный идентификатор', unique=True)

    # only for posts/comments from parser
    raw_html = models.TextField()

    @property
    def slug(self):
        return self.slug_prefix + str(self.remote_id)

class Post(WallAbstractModel):
    class Meta:
        verbose_name = u'Сообщение Вконтакте'
        verbose_name_plural = u'Сообщения Вконтакте'
        ordering = ['wall_owner_id','-date']

    # Владелец стены сообщения User or Group
    wall_owner_content_type = models.ForeignKey(ContentType, related_name='vkontakte_wall_posts')
    wall_owner_id = models.PositiveIntegerField()
    wall_owner = generic.GenericForeignKey('wall_owner_content_type', 'wall_owner_id')

    # Создатель/автор сообщения
    author_content_type = models.ForeignKey(ContentType, related_name='vkontakte_posts')
    author_id = models.PositiveIntegerField()
    author = generic.GenericForeignKey('author_content_type', 'author_id')

    # abstract field for correct deleting group and user models in admin
    group_wall = generic.GenericForeignKey('wall_owner_content_type', 'wall_owner_id')
    user_wall = generic.GenericForeignKey('wall_owner_content_type', 'wall_owner_id')
    group = generic.GenericForeignKey('author_content_type', 'author_id')
    user = generic.GenericForeignKey('author_content_type', 'author_id')

    date = models.DateTimeField(u'Время сообщения')
    text = models.TextField(u'Текст записи')

    comments = models.PositiveIntegerField(u'Кол-во комментариев', default=0)
    likes = models.PositiveIntegerField(u'Кол-во лайков', default=0)
    reposts = models.PositiveIntegerField(u'Кол-во репостов', default=0)

    like_users = models.ManyToManyField(User, blank=True, related_name='like_posts')
    repost_users = models.ManyToManyField(User, blank=True, related_name='repost_posts')

    #{u'photo': {u'access_key': u'5f19dfdc36a1852824',
    #u'aid': -7,
    #u'created': 1333664090,
    #u'height': 960,
    #u'owner_id': 2462759,
    #u'pid': 281543621,
    #u'src': u'http://cs9733.userapi.com/u2462759/-14/m_fdad45ec.jpg',
    #u'src_big': u'http://cs9733.userapi.com/u2462759/-14/x_60b1aed1.jpg',
    #u'src_small': u'http://cs9733.userapi.com/u2462759/-14/s_d457021e.jpg',
    #u'src_xbig': u'http://cs9733.userapi.com/u2462759/-14/y_b5a67b8d.jpg',
    #u'src_xxbig': u'http://cs9733.userapi.com/u2462759/-14/z_5a64a153.jpg',
    #u'text': u'',
    #u'width': 1280},
    #u'type': u'photo'}

    #u'attachments': [{u'link': {u'description': u'',
    #u'image_src': u'http://cs6030.userapi.com/u2462759/-2/x_cb9c00f8.jpg',
    #u'title': u'SAAB_9000_CD_2_0_Turbo_190_k.jpg',
    #u'url': u'http://www.yauto.cz/includes/img/inzerce/SAAB_9000_CD_2_0_Turbo_190_k.jpg'},
    #u'type': u'link'}],
    #attachments - содержит массив объектов, которые присоединены к текущей записи (фотографии, ссылки и т.п.). Более подробная информация представлена на странице Описание поля attachments
    attachments = models.TextField()
    media = models.TextField()

    #{u'coordinates': u'55.6745689498 37.8724562529',
    #u'place': {u'city': u'Moskovskaya oblast',
    #u'country': u'Russian Federation',
    #u'title': u'Shosseynaya ulitsa, Moskovskaya oblast'},
    #u'type': u'point'}
    #geo - если в записи содержится информация о местоположении, то она будет представлена в данном поле. Более подробная информация представлена на странице Описание поля geo
    geo = models.TextField()

    signer_id = models.PositiveIntegerField(null=True, help_text=u'Eсли запись была опубликована от имени группы и подписана пользователем, то в поле содержится идентификатор её автора')
    # могут быть негативные id, это группы или страницы
    copy_owner_id = models.IntegerField(null=True, help_text=u'Eсли запись является копией записи с чужой стены, то в поле содержится идентификатор владельца стены у которого была скопирована запись')
    copy_post_id = models.PositiveIntegerField(null=True, help_text=u'Если запись является копией записи с чужой стены, то в поле содержится идентфикатор скопированной записи на стене ее владельца')
    copy_text = models.TextField(u'Комментарий при репосте', help_text=u'Если запись является копией записи с чужой стены и при её копировании был добавлен комментарий, его текст содержится в данном поле')

    # not in API
    post_source = models.TextField()
    online = models.PositiveSmallIntegerField(null=True)
    reply_count = models.PositiveSmallIntegerField(null=True)

    objects = models.Manager()
    remote = PostRemoteManager(remote_pk=('remote_id',), methods={
        'get': 'get',
    })

    @property
    def on_group_wall(self):
        return self.wall_owner_content_type == ContentType.objects.get_for_model(Group)
    @property
    def on_user_wall(self):
        return self.wall_owner_content_type == ContentType.objects.get_for_model(User)

    def __unicode__(self):
        return '%s: %s' % (unicode(self.wall_owner), self.text)

    def save(self, *args, **kwargs):
        # check strings for good encoding
        # there is problems to save users with bad encoded activity strings like user ID=88798245
#        try:
#            self.text.encode('utf-16').decode('utf-16')
#        except UnicodeDecodeError:
#            self.text = ''

        # TODO: move this checking and other one to universal place
        # set exactly right Group or User contentTypes, not a child
        for field_name in ['wall_owner', 'author']:
            for allowed_model in [Group, User]:
                if isinstance(getattr(self, field_name), allowed_model):
                    setattr(self, '%s_content_type' % field_name, ContentType.objects.get_for_model(allowed_model))
                    break

        # check is generic fields has correct content_type
        allowed_ct_ids = [ct.id for ct in ContentType.objects.get_for_models(Group, User).values()]
        if self.wall_owner_content_type.id not in allowed_ct_ids:
            raise ValueError("'wall_owner' field should be Group or User instance, not %s" % self.wall_owner_content_type)
        if self.author_content_type.id not in allowed_ct_ids:
            raise ValueError("'author' field should be Group or User instance, not %s" % self.author_content_type)

        return super(Post, self).save(*args, **kwargs)

    def parse(self, response):

        for field_name in ['comments','likes','reposts']:
            if field_name in response and 'count' in response[field_name]:
                setattr(self, field_name, response.pop(field_name)['count'])

        # parse over API only for user's walls
        self.wall_owner = User.objects.get_or_create(remote_id=response.pop('to_id'))[0]
        self.author = User.objects.get_or_create(remote_id=response.pop('from_id'))[0]

        if 'attachment' in response:
            response.pop('attachment')
        super(Post, self).parse(response)

        self.remote_id = '%s_%s' % (self.wall_owner.remote_id, self.remote_id)

    def fetch_comments(self, *args, **kwargs):
        if self.on_group_wall:
            return Comment.remote.fetch_group_post(post=self, *args, **kwargs)
        elif self.on_user_wall:
            return Comment.remote.fetch_user_post(post=self, *args, **kwargs)

    def fetch_likes(self, offset=0):
        '''
        Update and save fields:
            * likes - count of likes
        Update relations:
            * like_users - users, who likes this post
        '''

        post_data = {
            'act': 'show',
            'al': 1,
            'w': 'likes/wall%s' % self.remote_id,
        }

        if offset == 0:
            number_on_page = 120
            post_data['loc'] = 'wall%s' % self.remote_id,
        else:
            number_on_page = 60
            post_data['offset'] = offset

        log.debug('Fetching likes of post "%s" of group "%s", offset %d' % (self.remote_id, self.wall_owner, offset))

        parser = VkontakteWallParser().request('/wkview.php', data=post_data)

        if offset == 0:
            try:
                self.likes = int(parser.content_bs.find('a', {'id': 'wk_likes_tablikes'}).find('nobr').text.split()[0])
                self.save()
            except:
                log.warning('Strange markup of first page likes response: "%s"' % parser.content)
            self.like_users.clear()

        #<div class="wk_likes_liker_row inl_bl" id="wk_likes_liker_row722246">
        #  <div class="wk_likes_likerph_wrap" onmouseover="WkView.likesBigphOver(this, 722246)">
        #    <a class="wk_likes_liker_ph" href="/kicolenka">
        #      <img class="wk_likes_liker_img" src="http://cs418825.vk.me/v418825246/6cf8/IBbSfmDz6R8.jpg" width="100" height="100" />
        #    </a>
        #  </div>
        #  <div class="wk_likes_liker_name"><a class="wk_likes_liker_lnk" href="/kicolenka">Оля Киселева</a></div>
        #</div>

        items = parser.content_bs.findAll('div', {'class': re.compile(r'^wk_likes_liker_row')})
        for item in items:
            user_link = item.find('a', {'class': 'wk_likes_liker_lnk'})
            user = User.remote.get_by_slug(user_link['href'][1:])
            if user:
                user.set_name(user_link.text)
                user.photo = item.find('img', {'class': 'wk_likes_liker_img'})['src']
                user.save()
                self.like_users.add(user)

        if len(items) == number_on_page:
            self.fetch_likes(offset=offset+number_on_page)

    def fetch_reposts(self, offset=0):
        '''
        Update and save fields:
            * reposts - count of reposts
        Update relations
            * repost_users - users, who repost this post
        '''
        post_data = {
            'act': 'show',
            'al': 1,
            'w': 'shares/wall%s' % self.remote_id,
        }

        if offset == 0:
            number_on_page = 40
            post_data['loc'] = 'wall%s' % self.remote_id,
        else:
            number_on_page = 20
            post_data['offset'] = offset

        log.debug('Fetching reposts of post "%s" of group "%s", offset %d' % (self.remote_id, self.wall_owner, offset))

        parser = VkontakteWallParser().request('/wkview.php', data=post_data)

        if offset == 0:
            try:
                self.reposts = int(parser.content_bs.find('a', {'id': 'wk_likes_tabshares'}).find('nobr').text.split()[0])
                self.save()
            except:
                log.warning('Strange markup of first page shares response: "%s"' % parser.content)
            self.repost_users.clear()

        #<div id="post65120659_2341" class="post post_copy" onmouseover="wall.postOver('65120659_2341')" onmouseout="wall.postOut('65120659_2341')" data-copy="-16297716_126261" onclick="wall.postClick('65120659_2341', event)">
        #  <div class="post_table">
        #    <div class="post_image">
        #      <a class="post_image" href="/vano0ooooo"><img src="/images/camera_c.gif" width="50" height="50"/></a>
        #    </div>
        #      <div class="wall_text"><a class="author" href="/vano0ooooo" data-from-id="65120659">Иван Панов</a> <div id="wpt65120659_2341"></div><table cellpadding="0" cellspacing="0" class="published_by_wrap">

        items = parser.content_bs.findAll('div', {'id': re.compile('^post')})
        for item in items:
            user_link = item.find('a', {'class': 'author'})
            user = User.remote.get_by_slug(user_link['href'][1:])
            if user:
                user.set_name(user_link.text)
                user.photo = item.find('a', {'class': 'post_image'}).find('img')['src']
                user.save()
                self.repost_users.add(user)

        if len(items) == number_on_page:
            self.fetch_reposts(offset=offset+number_on_page)

class Comment(WallAbstractModel):
    class Meta:
        verbose_name = u'Коментарий сообщения Вконтакте'
        verbose_name_plural = u'Комментарии сообщений Вконтакте'
        ordering = ['post','-date']

    remote_pk_field = 'cid'

    post = models.ForeignKey(Post, verbose_name=u'Пост', related_name='wall_comments')

    # Владелец стены сообщения User or Group (декомпозиция от self.post для фильтра в админке)
    wall_owner_content_type = models.ForeignKey(ContentType, related_name='vkontakte_wall_comments')
    wall_owner_id = models.PositiveIntegerField()
    wall_owner = generic.GenericForeignKey('wall_owner_content_type', 'wall_owner_id')

    # Автор комментария
    author_content_type = models.ForeignKey(ContentType, related_name='comments')
    author_id = models.PositiveIntegerField()
    author = generic.GenericForeignKey('author_content_type', 'author_id')

    from_id = models.IntegerField(null=True) # strange value, seems to be equal to author

    # Это ответ пользователю
    reply_for_content_type = models.ForeignKey(ContentType, null=True, related_name='replies')
    reply_for_id = models.PositiveIntegerField(null=True)
    reply_for = generic.GenericForeignKey('reply_for_content_type', 'reply_for_id')

    reply_to = models.ForeignKey('self', null=True, verbose_name=u'Это ответ на комментарий')

    # abstract field for correct deleting group and user models in admin
    group = generic.GenericForeignKey('author_content_type', 'author_id')
    user = generic.GenericForeignKey('author_content_type', 'author_id')
    group_wall_reply = generic.GenericForeignKey('reply_for_content_type', 'reply_for_id')
    user_wall_reply = generic.GenericForeignKey('reply_for_content_type', 'reply_for_id')

    date = models.DateTimeField(u'Время комментария')
    text = models.TextField(u'Текст комментария')

    likes = models.PositiveIntegerField(u'Кол-во лайков', default=0)

    objects = models.Manager()
    remote = CommentRemoteManager(remote_pk=('remote_id',), methods={
        'get': 'getComments',
    })

    def save(self, *args, **kwargs):
        self.wall_owner = self.post.wall_owner

        # TODO: move this checking and other one to universal place
        # set exactly right Group or User contentTypes, not a child
        for field_name in ['reply_for', 'author']:
            for allowed_model in [Group, User]:
                if isinstance(getattr(self, field_name), allowed_model):
                    setattr(self, '%s_content_type' % field_name, ContentType.objects.get_for_model(allowed_model))
                    break

        allowed_ct_ids = [ct.id for ct in  ContentType.objects.get_for_models(Group, User).values()]
        if self.author_content_type.id not in allowed_ct_ids:
            raise ValueError("'author' field should be Group or User instance, not %s" % self.author_content_type)
        if self.reply_for_content_type and self.reply_for_content_type.id not in allowed_ct_ids:
            raise ValueError("'reply_for' field should be Group or User instance, not %s" % self.reply_for_content_type)

        return super(Comment, self).save(*args, **kwargs)

    def parse(self, response):
        super(Comment, self).parse(response)

        if '_' not in str(self.remote_id):
            self.remote_id = '%s_%s' % (self.post.remote_id.split('_')[0], self.remote_id)

        for field_name in ['likes']:
            if field_name in response and 'count' in response[field_name]:
                setattr(self, field_name, response.pop(field_name)['count'])

        self.author = User.objects.get_or_create(remote_id=response['uid'])[0]

        if 'reply_to_uid' in response:
            self.reply_for = User.objects.get_or_create(remote_id=response['reply_to_uid'])[0]
        if 'reply_to_cid' in response:
            try:
                self.reply_to = Comment.objects.get(remote_id=response['reply_to_cid'])
            except:
                pass

Group.add_to_class('wall_posts', generic.GenericRelation(Post, content_type_field='wall_owner_content_type', object_id_field='wall_owner_id', related_name='group_wall', verbose_name=u'Сообщения на стене'))
User.add_to_class('wall_posts', generic.GenericRelation(Post, content_type_field='wall_owner_content_type', object_id_field='wall_owner_id', related_name='user_wall', verbose_name=u'Сообщения на стене'))

Group.add_to_class('posts', generic.GenericRelation(Post, content_type_field='author_content_type', object_id_field='author_id', related_name='group', verbose_name=u'Сообщения'))
User.add_to_class('posts', generic.GenericRelation(Post, content_type_field='author_content_type', object_id_field='author_id', related_name='user', verbose_name=u'Сообщения'))

Group.add_to_class('comments', generic.GenericRelation(Comment, content_type_field='author_content_type', object_id_field='author_id', related_name='group', verbose_name=u'Комментарии'))
User.add_to_class('comments', generic.GenericRelation(Comment, content_type_field='author_content_type', object_id_field='author_id', related_name='user', verbose_name=u'Комментарии'))

Group.add_to_class('replies', generic.GenericRelation(Comment, content_type_field='reply_for_content_type', object_id_field='reply_for_id', related_name='group_wall_reply', verbose_name=u'Ответы на комментарии'))
User.add_to_class('replies', generic.GenericRelation(Comment, content_type_field='reply_for_content_type', object_id_field='reply_for_id', related_name='user_wall_reply', verbose_name=u'Ответы на комментарии'))