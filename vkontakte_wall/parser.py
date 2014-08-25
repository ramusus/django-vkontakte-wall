# -*- coding: utf-8 -*-
from datetime import datetime
from django.dispatch.dispatcher import Signal
from vkontakte_api.parser import VkontakteParser, VkontakteParseError
import re

post_parsed = Signal(providing_args=['instance', 'raw_html'])
comment_parsed = Signal(providing_args=['instance', 'raw_html'])

def get_object_by_slug(slug):
    from vkontakte_users.models import User
    from vkontakte_groups.models import Group
    instance = User.remote.get_by_slug(slug)
    if not instance:
        instance = Group.remote.get_by_slug(slug)
    return instance

class VkontakteWallParser(VkontakteParser):

    def parse_container_date(self, container):

        text = container.find('span', {'class': re.compile('^rel_date')})
        if text:
            return self.parse_date(text.text)
        else:
            raise VkontakteParseError("Impossible to find date container in %s" % container)

    def parse_comment(self, content, wall_owner=None):
        from models import Comment

        remote_id = content['id'][4:]
        try:
            instance = Comment.objects.get(remote_id=remote_id)
        except Comment.DoesNotExist:
            instance = Comment(remote_id=remote_id)

        comment_text = content.find('div', {'class': 'fw_reply_text'})
        if comment_text:
            instance.text = comment_text.text

        # date
        instance.date = self.parse_container_date(content)
        # likes
        instance.likes = self.parse_container_likes(content, 'like_count fl_l')

        # author
        users = content.findAll('a', {'class': 'fw_reply_author'})
        slug = users[0]['href'][1:]
        if wall_owner and wall_owner.screen_name == slug:
            instance.author = wall_owner
        else:
            avatar = content.find('a', {'class': 'fw_reply_thumb'}).find('img')['src']
            name_parts = users[0].text.split(' ')

            user = get_object_by_slug(slug)
            if user:
                user.first_name = name_parts[0]
                if len(name_parts) > 1:
                    user.last_name = name_parts[1]
                user.photo = avatar
                user.save()
                instance.author = user

        if len(users) == 2:
            # this comment is answer
            slug = users[1]['href'][1:]
            if wall_owner and wall_owner.screen_name == slug:
                instance.reply_for = wall_owner
            else:
                instance.reply_for = get_object_by_slug(slug)
                # имя в падеже, аватара нет
                # чтобы получть текст и ID родительского коммента нужно отправить:
                #http://vk.com/al_wall.php
                #act:post_tt
                #al:1
                #post:-16297716_126263
                #reply:1

        instance.fetched = datetime.now()

        comment_parsed.send(sender=Comment, instance=instance, raw_html=str(content))
        return instance

    def parse_post(self, content, wall_owner):
        from models import Post
        from vkontakte_users.models import User

        remote_id = content['id'][4:]
        try:
            instance = Post.objects.get(remote_id=remote_id)
        except Post.DoesNotExist:
            instance = Post(remote_id=remote_id)

        post_text = content.find('div', {'class': 'wall_post_text'})
        if post_text:
            instance.text = post_text.text

        # date
        instance.date = self.parse_container_date(content)
        # likes
        instance.likes = self.parse_container_likes(content, 'post_like_count fl_l')

        # comments
        show_comments = content.find('div', {'class': 'wrh_text'})
        if show_comments:
            comments_words = show_comments.text.split(' ')
            if len(comments_words) in [3,4]:
                # Показать все 95 комментариев
                # Показать 91 комментарий
                instance.comments = int(comments_words[-2])
            elif len(comments_words) == 6:
                # Показать последние 100 комментариев из 170
                instance.comments = int(comments_words[-1])
            else:
                raise VkontakteParseError("Error number of words in show all comments message: '%s'" % show_comments.text.encode('utf-8'))
        else:
            instance.comments = len(content.findAll('div', {'class': 'reply_text'}))

        # author
        owner_slug = content.find('a', {'class': 'author'})['href'][1:]
        if wall_owner and wall_owner.screen_name == owner_slug:
            instance.author = wall_owner
        else:
            # author is someone else,
            # possible user, becouse the group can post only on it's own wall, where wall_owner is defined
            avatar = content.find('a', {'class': 'post_image'}).find('img')['src']
            name_parts = content.find('a', {'class': 'author'}).text.split(' ')

            user = get_object_by_slug(owner_slug)
            if user:
                user.first_name = name_parts[0]
                if len(name_parts) > 1:
                    user.last_name = name_parts[1]
                user.photo = avatar
                user.save()
                instance.author = user

        instance.fetched = datetime.now()
        if wall_owner:
            instance.wall_owner = wall_owner

        #<td>
        #  <div class="published_by_title"><a class="published_by" href="/yullz">Yulya Tsareva</a> </div>
        #  <div class="published_by_date"><a class="published_by_date"  href="/wall59124156_8301" onclick="return showWiki({w: 'wall59124156_8301'}, false, event);" >29 янв 2013 в 15:51</a></div>
        #</td>
        try:
            slug = content.find('a', {'class': 'published_by'})['href'][1:]
            post_link = content.find('a', {'class': 'published_by_date'})
            instance.copy_owner = get_object_by_slug(slug)
            instance.copy_post = Post.objects.get_or_create(remote_id=content.find('a', {'class': 'published_by_date'})['href'][5:], defaults={
                'wall_owner': instance.copy_owner,
                'date': self.parse_date(post_link.text)
            })[0]
        except:
            pass
        # <div class="published_comment wall_post_text">дядька молодец</div>
        copy_text = content.find('div', {'class': 'published_comment wall_post_text'})
        if copy_text:
            instance.copy_text = copy_text.text

        post_parsed.send(sender=Post, instance=instance, raw_html=str(content))
        return instance