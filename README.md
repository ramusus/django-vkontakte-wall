Django Vkontakte Wall
=====================

[![PyPI version](https://badge.fury.io/py/django-vkontakte-wall.png)](http://badge.fury.io/py/django-vkontakte-wall) [![Build Status](https://travis-ci.org/ramusus/django-vkontakte-wall.png?branch=master)](https://travis-ci.org/ramusus/django-vkontakte-wall) [![Coverage Status](https://coveralls.io/repos/ramusus/django-vkontakte-wall/badge.png?branch=master)](https://coveralls.io/r/ramusus/django-vkontakte-wall)

Приложение позволяет взаимодействовать со стенами Вконтакте, сообщениями и комментариями на них через Вконтакте API и парсер используя стандартные модели Django

Установка
---------

    pip install django-vkontakte-wall

В `settings.py` необходимо добавить:

    INSTALLED_APPS = (
        ...
        'oauth_tokens',
        'taggit',
        'vkontakte_api',
        'vkontakte_places',
        'vkontakte_users',
        'vkontakte_groups',
        'vkontakte_wall',
    )

    # oauth-tokens settings
    OAUTH_TOKENS_HISTORY = True                                         # to keep in DB expired access tokens
    OAUTH_TOKENS_VKONTAKTE_CLIENT_ID = ''                               # application ID
    OAUTH_TOKENS_VKONTAKTE_CLIENT_SECRET = ''                           # application secret key
    OAUTH_TOKENS_VKONTAKTE_SCOPE = ['ads,wall,photos,friends,stats']    # application scopes
    OAUTH_TOKENS_VKONTAKTE_USERNAME = ''                                # user login
    OAUTH_TOKENS_VKONTAKTE_PASSWORD = ''                                # user password
    OAUTH_TOKENS_VKONTAKTE_PHONE_END = ''                               # last 4 digits of user mobile phone

Покрытие методов API
--------------------

* [wall.get](http://vk.com/dev/wall.get) – возвращает список записей со стены;
* [wall.getById](http://vk.com/dev/wall.getById) – получает записи со стен пользователей по их идентификаторам;
* [wall.getLikes](http://vk.com/dev/wall.getLikes) – получает информацию о пользователях которым нравится данная запись;
* [wall.post](http://vk.com/dev/wall.post) – публикует новую запись на своей или чужой стене; 
* [wall.edit](http://vk.com/dev/wall.edit) – редактирует запись на стене;
* [wall.delete](http://vk.com/dev/wall.delete) – удаляет запись со стены;
* [wall.restore](http://vk.com/dev/wall.restore) – восстанавливает удаленную запись на стене пользователя;
* [wall.getComments](http://vk.com/dev/wall.getComments) – получает комментарии к записи на стене пользователя;
* [wall.addComments](http://vk.com/dev/wall.addComments) – добавляет комментарий к записи на стене пользователя или сообщества;
* [wall.editComments](http://vk.com/dev/wall.editComments) – редактирует комментарий на стене пользователя или сообщества;
* [wall.deleteComments](http://vk.com/dev/wall.deleteComments) – удаляет комментарий текущего пользователя к записи на своей или чужой стене;
* [wall.restoreComments](http://vk.com/dev/wall.restoreComments) – восстанавливает комментарий текущего пользователя к записи на своей или чужой стене;

В планах:


Использование парсера
---------------------

* Получение сообщений со стены группы; *
* Получение комментариев сообщения со стены группы; *
* Получение лайков сообщения; *
* Получение перепостов сообщения.

(*) Дублирование функционала API

Примеры использования
---------------------

### Получение сообщений по их идентификаторам

    >>> from vkontakte_wall.models import Post
    >>> Post.remote.fetch(ids=['5223304_130', '-16297716_126261'])
    [<Post: ...>, <Post: ...>]

### Получение сообщений со стены пользователя через метод пользователя

    >>> from vkontakte_users.models import User
    >>> user = User.remote.fetch(ids=[1])[0]
    >>> user.fetch_posts()
    [<Post: ...>, <Post: ...>, <Post: ...>, '...(remaining elements truncated)...']

Сообщения пользователя доступны через менеджер

    >>> user.wall_posts.count()
    432

Комментарии всех сообщений пользователя доступны через менеджер

    >>> user.wall_comments.count()
    73637

### Получение сообщений со стены пользователя через менеджер

    >>> from vkontakte_users.models import User
    >>> user = User.remote.fetch(ids=[1])[0]
    >>> Post.remote.fetch_user_wall(user=user)
    [<Post: ...>, <Post: ...>, <Post: ...>, '...(remaining elements truncated)...']

### Получение сообщений со стены группы через метод группы

    >>> from vkontakte_groups.models import Group
    >>> group = Group.remote.fetch(ids=[16297716])[0]
    >>> group.fetch_posts()
    [<Post: Coca-Cola: ...>, <Post: Coca-Cola: ...>, '...(remaining elements truncated)...']

Сообщения группы доступны через менеджер

    >>> group.wall_posts.count()
    5498

Комментарии всех сообщений группы доступны через менеджер

    >>> group.wall_comments.count()
    73637

### Получение сообщений со стены группы через менеджер

    >>> from vkontakte_groups.models import Group
    >>> group = Group.remote.fetch(ids=[16297716])[0]
    >>> Post.remote.fetch_group_wall(group=group)
    [<Post: ...>, <Post: ...>, <Post: ...>, '...(remaining elements truncated)...']

### Получение комментариев сообщения со стены группы через менеджер

    >>> from vkontakte_users.models import User
    >>> user = User.remote.fetch(ids=[1])[0]
    >>> post = user.wall_posts.all()[0]
    >>> Comment.remote.fetch_user_post(post=post)
    [<Comment: ...>, <Comment: ...>, <Comment: ...>, '...(remaining elements truncated)...']


### Публикация записи на стене

       >>> post = Post.objects.create(**param)
       >>> print post.text
       'message'

       или

       >>> post = Post()
       >>> post.text = 'blah...'
       ....
       >>> post.save()
       >>> post.text
       'message'
    

### Редактирование опубликованной записи

        >>> post = Post.objects.get(remote_id='5223304_130')
        >>> post.text = 'Edited message' 
        >>> post.save()
        >>> post.text
        'Edited message'

### Удаление опупбликованной записи

       >>> post.delete()  # Запись не удаляется из БД, 
       >>> post.archived  
       True               # вместо этого аттрибуту archived присваивается True

### Востановление удаленной записи

       >>> post.restore() # Запись не создается заново    
       >>> post.archived  
       False               # вместо этого аттрибуту archived присваивается False


### Публикация коментария к записи на стене

        >>> test_comment = Comment.objects.create(**commpent_param)
        >>> test_comment
        <Comment:...>

        или

        >>> comment = Comment()
        >>> comment.text = 'text'
        ....
        >>> comment.save()
        >>> comment.remote_id
        '123123_123'
        >>> comment.text
        'text'


### Редактирование опубликованного комментария

        >>> edited_message = 'Edited comment message'
        >>> comment = Comment.objects.get(...)
        >>> comment.text = 'Edited comment message'
        >>> comment.save()
        >>> comment.text
        'Edited comment message'

### Удаление опупбликованного комментария

       >>> test_comment.delete()  # Запись не удаляется из БД, 
       >>> test_comment.archived  
       True               # вместо этого аттрибуту archived присваивается True

### Востановление удаленного комментария

       >>> test_comment.restore() # Запись не создается заново    
       >>> test_comment.archived  
       False               # вместо этого аттрибуту archived присваивается False


