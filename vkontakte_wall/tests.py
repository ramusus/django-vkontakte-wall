# -*- coding: utf-8 -*-
from django.test import TestCase
from models import Post, Comment
from factories import PostFactory, UserFactory, GroupFactory, CommentFactory
from vkontakte_users.models import User
from datetime import datetime
import simplejson as json
import mock

USER_ID = 5223304
POST_ID = '5223304_130'
GROUP_ID = 16297716
GROUP_SCREEN_NAME = 'cocacola'
GROUP_POST_ID = '-16297716_126261'
GROUP_COMMENT_ID = '-16297716_126262'
OPEN_WALL_GROUP_ID = 19391365
OPEN_WALL_GROUP_SCREEN_NAME = 'nokia'
OWNER_ID = -59154616

TRAVIS_USER_ID = 201164356
TR_POST_ID = '201164356_15'
POST_WITH_COMMENT = '-59154616_332'
POST_OWN_ID = '-59154616_330'


class VkontakteWallTest(TestCase):

    def test_fetch_posts(self, *args, **kwargs):

        self.assertTrue(Post.objects.count() == 0)

        posts = Post.remote.fetch(ids=[POST_ID, GROUP_POST_ID])
        self.assertTrue(len(posts) == Post.objects.count() == 2)

    def fetch_post_comments_recursive_calls_ammount_side_effect(*args, **kwargs):
        comments_count = 100 if kwargs['offset'] == 0 else 6
        comments = [CommentFactory.create() for i in range(comments_count)]
        return Comment.objects.filter(pk__in=[comment.pk for comment in comments])

    @mock.patch('vkontakte_wall.models.Comment.remote.fetch', side_effect=fetch_post_comments_recursive_calls_ammount_side_effect)
    def test_fetch_post_comments_recursive_calls_ammount(self, fetch_method, *args, **kwargs):

        post = PostFactory.create(remote_id=TR_POST_ID)
        comments = post.fetch_comments(sort='desc', all=True)

        self.assertTrue(len(comments) > 105)
        self.assertEqual(fetch_method.called, True)
        self.assertEqual(fetch_method.call_count, 2)
        self.assertEqual(fetch_method.call_args_list[0][1]['offset'], 0)
        self.assertEqual(fetch_method.call_args_list[1][1]['offset'], 100)

    def test_fetch_user_wall(self):

        owner = UserFactory.create(remote_id=TRAVIS_USER_ID)

        self.assertEqual(Post.objects.count(), 0)

        posts = owner.fetch_posts()

        self.assertTrue(len(posts) > 0)
        self.assertEqual(Post.objects.count(), len(posts))
        self.assertEqual(posts[0].wall_owner, owner)

        owner.fetch_posts(all=True)
        self.assertTrue(Post.objects.count() >= len(posts))

    def test_fetch_group_wall(self):

        group = GroupFactory.create(remote_id=GROUP_ID, screen_name=GROUP_SCREEN_NAME)

        self.assertEqual(Post.objects.count(), 0)

        posts = group.fetch_posts(count=10)

        self.assertEqual(posts[0].wall_owner, group)
        self.assertTrue(len(posts) == Post.objects.count() == 10)
        self.assertTrue(isinstance(posts[0].date, datetime))
        self.assertTrue(posts[0].likes + posts[1].likes > 0)
        self.assertTrue(posts[0].comments + posts[1].comments > 0)
        self.assertTrue(len(posts[0].text) > 0)

        # testing `after` parameter
        after = Post.objects.order_by('date')[0].date

        Post.objects.all().delete()
        self.assertEqual(Post.objects.count(), 0)

        posts = group.fetch_posts(after=after)
        self.assertTrue(len(posts) == Post.objects.count() == 10)

        # testing `after` and `all` parameters and returning less than all scope of posts
        Post.objects.all().delete()
        self.assertEqual(Post.objects.count(), 0)

        group.fetch_posts(count=30)
        posts = group.fetch_posts(after=after, all=True)
        self.assertEqual(Post.objects.count(), 30)
        self.assertEqual(len(posts), 10)

    def test_fetch_group_open_wall(self):

        group = GroupFactory.create(remote_id=OPEN_WALL_GROUP_ID, screen_name=OPEN_WALL_GROUP_SCREEN_NAME)

        self.assertEqual(Post.objects.count(), 0)
        self.assertEqual(User.objects.count(), 0)

        count = 10
        posts = group.fetch_posts(own=0, count=count, extended=1)

        self.assertEqual(len(posts), count)
        self.assertEqual(Post.objects.count(), count)
        self.assertTrue(User.objects.count() > 0)
        self.assertTrue(Post.objects.exclude(author_id=None).count() > 0)

    def test_fetch_user_post_comments(self):
        owner = UserFactory.create(remote_id=TRAVIS_USER_ID)
        post = PostFactory.create(remote_id=TR_POST_ID, wall_owner=owner)
        self.assertEqual(Comment.objects.count(), 0)

        comments = post.fetch_comments()

        self.assertTrue(len(comments) > 0)
        self.assertEqual(Comment.objects.count(), len(comments))
        self.assertEqual(comments[0].post, post)

        post.fetch_comments(all=True)
#        self.assertTrue(Comment.objects.count() > len(comments)) only 1 comment

    @mock.patch('vkontakte_users.models.User.remote.get_by_slug', side_effect=lambda s: UserFactory.create())
    def test_fetch_group_post_comments(self, *args, **kwargs):
        group = GroupFactory.create(remote_id=GROUP_ID, screen_name=GROUP_SCREEN_NAME)
        post = PostFactory.create(remote_id=GROUP_POST_ID, wall_owner=group)
        self.assertEqual(Comment.objects.count(), 0)

        comments = post.fetch_comments(sort='desc', count=90)

        self.assertTrue(len(comments) == Comment.objects.count() == post.wall_comments.count() == 90)
        self.assertEqual(comments[0].post, post)
        self.assertEqual(comments[0].wall_owner, group)

        # testing `after` parameter
        after = Comment.objects.order_by('date')[0].date

        Comment.objects.all().delete()
        self.assertEqual(Comment.objects.count(), 0)

        comments = post.fetch_comments(sort='desc', after=after, count=100)
        self.assertTrue(len(comments) == Comment.objects.count() == post.wall_comments.count() == 90)

        # testing `after` and `all` parameters
        Comment.objects.all().delete()
        self.assertEqual(Comment.objects.count(), 0)

        comments = post.fetch_comments(sort='desc', after=after, all=True)
        self.assertTrue(len(comments) == Comment.objects.count() == post.wall_comments.count() == 90)

    @mock.patch('vkontakte_users.models.User.remote.get_by_slug', side_effect=lambda s: UserFactory.create())
    def test_fetch_post_reposts(self, *args, **kwargs):

        group = GroupFactory.create(remote_id=GROUP_ID)
        post = PostFactory.create(remote_id=GROUP_POST_ID, wall_owner=group)

        self.assertTrue(post.repost_users.count() == 0)
        users = post.fetch_reposts(all=True)
        self.assertTrue(post.reposts >= 20)
        self.assertTrue(post.reposts == post.repost_users.count() == users.count())

        group = GroupFactory.create(remote_id=36948301)
        post = PostFactory.create(remote_id='-36948301_13599', wall_owner=group)

        self.assertTrue(post.reposts == post.repost_users.count() == 0)
        users = post.fetch_reposts(all=True)
        self.assertTrue(post.reposts == 1)
        self.assertTrue(post.reposts == post.repost_users.count() == users.count())

    @mock.patch('vkontakte_users.models.User.remote.get_by_slug', side_effect=lambda s: UserFactory.create())
    def test_fetch_post_likes(self, *args, **kwargs):

        group = GroupFactory.create(remote_id=GROUP_ID)
        post = PostFactory.create(remote_id=GROUP_POST_ID, wall_owner=group)

        self.assertTrue(post.likes == post.like_users.count() == 0)

        post.fetch_likes(source='parser')
        self.assertTrue(post.likes == post.like_users.count() > 120)

        post.like_users.all().delete()
        post.likes = 0
        post.save()
        self.assertTrue(post.likes == post.like_users.count() == 0)

        post.fetch_likes(all=True)
        self.assertTrue(post.likes == post.like_users.count() > 120)

    @mock.patch('vkontakte_users.models.User.remote.get_by_slug', side_effect=lambda s: UserFactory.create())
    def test_fetch_comment_likes(self, *args, **kwargs):
        user = UserFactory.create(remote_id=TRAVIS_USER_ID)
        post = PostFactory.create(remote_id=TR_POST_ID, wall_owner=user)
        comment = post.fetch_comments()[0]

        self.assertTrue(comment.like_users.count() == 0)

        comment.fetch_likes(all=True)
        self.assertTrue(comment.like_users.count() >= 1)
        self.assertTrue(comment.likes >= 1)

    def test_parse_post(self):
        response = '''{"comments": {"can_post": 0, "count": 4},
                 "date": 1298365200,
                 "from_id": 55555,
                 "geo": {"coordinates": "55.6745689498 37.8724562529",
                  "place": {"city": "Moskovskaya oblast",
                   "country": "Russian Federation",
                   "title": "Shosseynaya ulitsa, Moskovskaya oblast"},
                  "type": "point"},
                 "id": 465,
                 "likes": {"can_like": 1, "can_publish": 1, "count": 10, "user_likes": 0},
                 "online": 1,
                 "post_source": {"type": "api"},
                 "reply_count": 0,
                 "reposts": {"count": 3, "user_reposted": 0},
                 "text": "qwerty",
                 "to_id": 201164356}
            '''
        instance = Post()
        owner = UserFactory.create(remote_id=201164356)  # Travis Djangov
        author = UserFactory.create(remote_id=55555)
        instance.parse(json.loads(response))
        instance.save()

        self.assertTrue(instance.remote_id.startswith('201164356_'))
        self.assertEqual(instance.wall_owner, owner)
        self.assertEqual(instance.author, author)
        self.assertEqual(instance.reply_count, 0)
        self.assertEqual(instance.likes, 10)
        self.assertEqual(instance.reposts, 3)
        self.assertEqual(instance.comments, 4)
        self.assertEqual(instance.text, 'qwerty')
        self.assertTrue(isinstance(instance.date, datetime))

    def test_parse_comments(self):

        response = '''{"response":[6,
            {"cid":2505,"uid":16271479,"date":1298365200,"text":"Добрый день , кароче такая идея когда опросы создаешь вместо статуса - можно выбрать аудитории опрашиваемых, например только женский или мужской пол могут участвовать (то бишь голосовать в опросе)."},
            {"cid":2507,"uid":16271479,"date":1286105582,"text":"Это уже не практично, имхо.<br>Для этого делайте группу и там опрос, а в группу принимайте тех, кого нужно.","reply_to_uid":16271479,"reply_to_cid":2505},
            {"cid":2547,"uid":2943,"date":1286218080,"text":"Он будет только для групп благотворительных организаций."}]}
            '''
        group = GroupFactory.create(remote_id=OWNER_ID)
        post = PostFactory.create(remote_id=TR_POST_ID, wall_owner=group)
        #instance = Comment(post=post)
        instance = CommentFactory.create(post=post)
        author = UserFactory.create(remote_id=16271479)
        instance.parse(json.loads(response)['response'][1])
        instance.save()

        self.assertEqual(instance.remote_id, '201164356_2505')
        self.assertEqual(instance.text, u'Добрый день , кароче такая идея когда опросы создаешь вместо статуса - можно выбрать аудитории опрашиваемых, например только женский или мужской пол могут участвовать (то бишь голосовать в опросе).')
        self.assertEqual(instance.author, author)
        self.assertTrue(isinstance(instance.date, datetime))

        instance = Comment(post=post)
        instance.parse(json.loads(response)['response'][2])
        instance.save()

        self.assertEqual(instance.remote_id, '201164356_2507')
        self.assertEqual(instance.reply_for.remote_id, 16271479)

    def test_post_prepare_create_params(self):
        text = 'test text'
        expected_config = {
            'owner_id': OWNER_ID,
            'friends_only': 0,
            'from_group': '',
            'message': text,
            'attachments': u'',
            'services': '',
            'signed': 0,
            'publish_date': '',
            'lat': '',
            'long': '',
            'place_id': '',
            'post_id': ''
        }
        group = GroupFactory.create(remote_id=OWNER_ID)
        post = PostFactory.create()
        post.wall_owner = group
        post.text = text
        self.assertEqual(post.prepare_create_params(), expected_config)

    def test_post_prepare_update_params(self):
        group = GroupFactory.create(remote_id=OWNER_ID)
        post = PostFactory.create(remote_id='%s_17' % OWNER_ID, wall_owner=group)
        update_text = 'update text'
        expected_config = {
            'owner_id': OWNER_ID,
            'friends_only': 0,
            'from_group': '',
            'message': update_text,
            'attachments': u'',
            'services': '',
            'signed': 0,
            'publish_date': '',
            'lat': '',
            'long': '',
            'place_id': '',
            'post_id': '17'
        }
        post1 = Post.objects.get(id=post.id)
        post1.text = update_text
        self.assertEqual(post1.prepare_update_params(), expected_config)

    def test_post_prepare_delete_restore_params(self):
        group = GroupFactory.create(remote_id=OWNER_ID)
        post = PostFactory.create(remote_id='%s_17' % OWNER_ID, wall_owner=group)
        expected_params = {
            'owner_id': OWNER_ID,
            'post_id': '17',
        }
        self.assertEqual(post.prepare_delete_restore_params(), expected_params)

    def test_post_crud_methods(self):
        message = 'Test message'
        group = GroupFactory.create(remote_id=OWNER_ID)
        #user = UserFactory.create(remote_id=TRAVIS_USER_ID)
        mock_post = PostFactory.create(text=message, wall_owner=group)
        #mock_post = PostFactory.create(text=message, wall_owner=user)
        kwargs = {}
        for key in mock_post.__dict__:
            if not key.startswith('_'):
                kwargs[key] = mock_post.__dict__[key]
        del kwargs['id']
        del kwargs['remote_id']
        del kwargs['archived']
        kwargs['commit_remote'] = True

        #create by objects api
        post = Post.objects.create(**kwargs)
        post = mock_post

        self.assertTrue(post.remote_id > 0)
        self.assertEqual(post.text, kwargs['text'])

        # Update
        edited_message = 'Edited message with CRUD'
        post = Post.objects.get(id=post.id)
        post.text = edited_message
        post.save()
        self.assertEqual(post.text, edited_message)

        # Delete
        post.delete()
        post1 = Post.objects.get(id=post.id)
        self.assertTrue(post1.archived)

        # Restore
        post.restore()
        post1 = Post.objects.get(id=post.id)
        self.assertFalse(post1.archived)

        post.delete()

        # Create with save()
        kwargs = post.__dict__
        del kwargs['id']
        del kwargs['remote_id']
        del kwargs['archived']
        #post = Post()
        post = PostFactory.create()
        post.__dict__.update(kwargs)
        post.text = message + message
        post.save()

        self.assertTrue(post.remote_id > 0)
        self.assertEqual(post.text, message + message)

        post.delete()

    def test_comment_crud_methods(self):
        text = 'Test message'
        group = GroupFactory.create(remote_id=OWNER_ID)
        post = PostFactory.create(text=text, wall_owner=group)
        mock_comment = CommentFactory.create(text=text, post=post, wall_owner=group)
        kwargs = {}
        for key in mock_comment.__dict__:
            if not key.startswith('_'):
                kwargs[key] = mock_comment.__dict__[key]
        del kwargs['id']
        del kwargs['remote_id']
        del kwargs['archived']

        # Create
        comment = Comment.objects.create(**kwargs)

        self.assertTrue(comment.remote_id > 0)
        self.assertEqual(comment.text, text)

        # Update
        edited_message = 'Edited comment message'
        comment = Comment.objects.get(id=comment.id)
        comment.text = edited_message
        comment.save()

        self.assertEqual(comment.text, edited_message)

        # Delete
        comment.delete()
        comment1 = Comment.objects.get(id=comment.id)
        self.assertTrue(comment1.archived)

        # Restore
        comment.restore()
        comment1 = Comment.objects.get(id=comment.id)
        self.assertFalse(comment1.archived)

        # Create with save()
        kwargs = comment.__dict__
        del kwargs['id']
        del kwargs['remote_id']
        del kwargs['archived']
        comment = Comment()
        comment.__dict__.update(kwargs)
        comment.text = text + text
        comment.save()

        self.assertTrue(comment.remote_id > 0)
        self.assertEqual(comment.text, text + text)

        # remove template post
        post.delete()
