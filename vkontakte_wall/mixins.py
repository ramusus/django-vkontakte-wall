# -*- coding: utf-8 -*-
from datetime import datetime
import logging
import re

from django.db import models
from django.utils import timezone
from m2m_history.fields import ManyToManyHistoryField
from vkontakte_api.api import api_call
from vkontakte_api.decorators import fetch_all, atomic
from vkontakte_api.mixins import LikableModelMixin as LikableModelMixinBase
from vkontakte_api.models import MASTER_DATABASE
from vkontakte_users.models import User

from .parser import VkontakteWallParser

log = logging.getLogger('vkontakte_wall')


class LikableModelMixin(LikableModelMixinBase):

    class Meta:
        abstract = True

    @atomic
    def fetch_likes(self, source='api', *args, **kwargs):
        if source == 'api':
            return super(LikableModelMixin, self).fetch_likes(*args, **kwargs)
        else:
            return self.fetch_likes_parser(*args, **kwargs)

    @atomic
    def fetch_likes_parser(self, offset=0):
        '''
        Update and save fields:
            * likes - count of likes
        Update relations:
            * likes_users - users, who likes this post
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

        log.debug('Fetching likes of post "%s" of owner "%s", offset %d' % (
            self.remote_id, self.owner, offset))

        parser = VkontakteWallParser().request('/wkview.php', data=post_data)

        if offset == 0:
            try:
                self.likes_count = int(
                    parser.content_bs.find('a', {'id': 'wk_likes_tablikes'}).find('nobr').text.split()[0])
                self.save()
            except ValueError:
                return
            except:
                log.warning('Strange markup of first page likes response: "%s"' % parser.content)
            self.likes_users.clear()

        # <div class="wk_likes_liker_row inl_bl" id="wk_likes_liker_row722246">
        #  <div class="wk_likes_likerph_wrap" onmouseover="WkView.likesBigphOver(this, 722246)">
        #    <a class="wk_likes_liker_ph" href="/kicolenka">
        #      <img class="wk_likes_liker_img" src="http://cs418825.vk.me/v418825246/6cf8/IBbSfmDz6R8.jpg" width="100" height="100" />
        #    </a>
        #  </div>
        #  <div class="wk_likes_liker_name"><a class="wk_likes_liker_lnk" href="/kicolenka">Оля Киселева</a></div>
        # </div>

        items = parser.add_users(users=('div', {'class': re.compile(r'^wk_likes_liker_row')}),
                                 user_link=('a', {'class': 'wk_likes_liker_lnk'}),
                                 user_photo=('img', {'class': 'wk_likes_liker_img'}),
                                 user_add=lambda user: self.likes_users.add(user))

        if len(items) == number_on_page:
            self.fetch_likes_parser(offset=offset + number_on_page)
        else:
            return self.likes_users.all()


class RepostableModelMixin(models.Model):

    reposts_users = ManyToManyHistoryField(User, related_name='reposts_%(class)ss')
    reposts_count = models.PositiveIntegerField(u'Кол-во репостов', null=True, db_index=True)

    class Meta:
        abstract = True

    def parse(self, response):
        if 'reposts' in response:
            value = response.pop('reposts')
            if isinstance(value, int):
                response['reposts_count'] = value
            elif isinstance(value, dict) and 'count' in value:
                response['reposts_count'] = value['count']
        super(RepostableModelMixin, self).parse(response)

    @property
    def reposters(self):
        return [repost.author for repost in self.wall_reposts.all()]

    def fetch_reposts(self, source='api', *args, **kwargs):
        if source == 'api':
            return self.fetch_reposts_api(*args, **kwargs)
        else:
            return self.fetch_reposts_parser(*args, **kwargs)

    def fetch_reposts_api(self, *args, **kwargs):
        self.fetch_instance_reposts(*args, **kwargs)

        # update self.reposts_count
        reposts_count = self.reposts_users.get_query_set(only_pk=True).count()
        if reposts_count < self.reposts_count:
            log.warning('Fetched ammount of repost users less, than attribute `reposts` of post "%s": %d < %d' %
                        (self.remote_id, reposts_count, self.reposts_count))
        elif reposts_count > self.reposts_count:
            self.reposts_count = reposts_count
            self.save()

        return self.reposts_users.all()

    @atomic
    def fetch_instance_reposts(self, *args, **kwargs):
        resources = self.fetch_reposts_items(*args, **kwargs)
        if not resources:
            return self.__class__.objects.none()

        # TODO: still complicated to store reposts objects, may be it's task for another application
#         posts = Post.remote.parse_response(resources, extra_fields={'copy_post_id': self.pk})
#         Post.objects.filter(pk__in=set([Post.remote.get_or_create_from_instance(instance).pk
#         for instance in posts]))

        # positive ids -> only users
        # TODO: think about how to store reposts by groups
        timestamps = dict([(post['from_id'], post['date']) for post in resources if post['from_id'] > 0])
        ids_new = timestamps.keys()
        ids_current = self.reposts_users.get_query_set(only_pk=True).using(MASTER_DATABASE).exclude(time_from=None)
        ids_current_left = self.reposts_users.get_query_set_through().using(MASTER_DATABASE).exclude(time_to=None) \
            .values_list('user_id', flat=True)
        ids_add = set(ids_new).difference(set(ids_current))
        ids_remove = set(ids_current).difference(set(ids_new))
        # some of them may be already left for some reason or API error
        ids_unleft = set(ids_add).intersection(set(ids_current_left))
        ids_add = ids_add.difference(ids_unleft)

        # fetch new users
        User.remote.fetch(ids=ids_add, only_expired=True)

        # remove old reposts without time_from
        self.reposts_users.get_query_set_through().filter(time_from=None).delete()

        # try to find left users, that present in ids_add and make them unleft
        self.reposts_users.get_query_set_through().exclude(time_to=None).filter(
            user_id__in=ids_unleft).update(time_to=None)

        # add new reposts
        get_repost_date = lambda id: datetime.utcfromtimestamp(
            timestamps[id]).replace(tzinfo=timezone.utc) if id in timestamps else self.date

        m2m_model = self.reposts_users.through
        m2m_model.objects.bulk_create(
            [m2m_model(**{'user_id': id, 'post_id': self.pk, 'time_from': get_repost_date(id)}) for id in ids_add])

        # remove reposts
        self.reposts_users.get_query_set_through().filter(user_id__in=ids_remove).update(time_to=timezone.now())

    # не рекомендуется указывать default_count из-за бага паджинации репостов: https://vk.com/wall-51742963_6860
    @fetch_all(max_extra_calls=3)
    def fetch_reposts_items(self, offset=0, count=1000, *args, **kwargs):
        if count > 1000:
            raise ValueError("Parameter 'count' can not be more than 1000")

        # owner_id
        # идентификатор пользователя или сообщества, на стене которого находится запись. Если параметр не задан, то он считается равным идентификатору текущего пользователя.
        # Обратите внимание, идентификатор сообщества в параметре owner_id необходимо указывать со знаком "-" — например, owner_id=-1 соответствует идентификатору сообщества ВКонтакте API (club1)
        kwargs['owner_id'] = self.owner_remote_id
        # post_id
        # идентификатор записи на стене.
        kwargs['post_id'] = self.remote_id_short
        # offset
        # смещение, необходимое для выборки определенного подмножества записей.
        kwargs['offset'] = int(offset)
        # count
        # количество записей, которое необходимо получить.
        # положительное число, по умолчанию 20, максимальное значение 100
        kwargs['count'] = int(count)

        response = api_call('wall.getReposts', **kwargs)
        log.debug('Fetching reposts for post %s: %d returned, offset %d, count %d' %
                  (self.remote_id, len(response['items']), offset, count))
        return response['items']

    @atomic
    def fetch_reposts_parser(self, offset=0):
        '''
        OLD method via parser, may works incorrect
        Update and save fields:
            * reposts - count of reposts
        Update relations
            * reposts_users - users, who repost this post
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

        log.debug('Fetching reposts of post "%s" of owner "%s", offset %d' % (self.remote_id, self.owner, offset))

        parser = VkontakteWallParser().request('/wkview.php', data=post_data)
        if offset == 0:
            try:
                self.reposts_count = int(
                    parser.content_bs.find('a', {'id': 'wk_likes_tabshares'}).find('nobr').text.split()[0])
                self.save()
            except ValueError:
                return
            except:
                log.warning('Strange markup of first page shares response: "%s"' % parser.content)
            self.reposts_users.clear()

        # <div id="post65120659_2341" class="post post_copy" onmouseover="wall.postOver('65120659_2341')" onmouseout="wall.postOut('65120659_2341')" data-copy="-16297716_126261" onclick="wall.postClick('65120659_2341', event)">
        #  <div class="post_table">
        #    <div class="post_image">
        #      <a class="post_image" href="/vano0ooooo"><img src="/images/camera_c.gif" width="50" height="50"/></a>
        #    </div>
        #      <div class="wall_text"><a class="author" href="/vano0ooooo" data-from-id="65120659">Иван Панов</a> <div id="wpt65120659_2341"></div><table cellpadding="0" cellspacing="0" class="published_by_wrap">

        items = parser.add_users(users=('div', {'id': re.compile('^post\d'), 'class': re.compile('^post ')}),
                                 user_link=('a', {'class': 'author'}),
                                 user_photo=lambda item: item.find('a', {'class': 'post_image'}).find('img'),
                                 user_add=lambda user: self.reposts_users.add(user))

        if len(items) == number_on_page:
            self.fetch_reposts(offset=offset + number_on_page)
        else:
            return self.reposts_users.all()
