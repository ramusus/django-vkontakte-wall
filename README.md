# Django Vkontakte Wall

Приложение позволяет взаимодействовать со стенами Вконтакте, сообщениями и комментариями на них через Вконтакте API и парсер используя стандартные модели Django

## Установка

    pip install django-vkontakte-wall

В `settings.py` необходимо добавить:

    INSTALLED_APPS = (
        ...
        'vkontakte_api',
        'vkontakte_wall',
    )

## Примеры использования

### Получение сообщений со стены пользователя через метод пользователя

Для этого необходимо установить дополнительно приложение
[`django-vkontakte-users`](http://github.com/ramusus/django-vkontakte-users/) и добавить его в `INSTALLED_APPS`

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

Для этого необходимо установить дополнительно приложение
[`django-vkontakte-users`](http://github.com/ramusus/django-vkontakte-users/) и добавить его в `INSTALLED_APPS`

    >>> from vkontakte_users.models import User
    >>> user = User.remote.fetch(ids=[1])[0]
    >>> Post.remote.fetch_user_wall(user=user)
    [<Post: ...>, <Post: ...>, <Post: ...>, '...(remaining elements truncated)...']

### Получение сообщений со стены группы через метод группы

Для этого необходимо установить дополнительно приложение
[`django-vkontakte-groups`](http://github.com/ramusus/django-vkontakte-groups/) и добавить его в `INSTALLED_APPS`

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

Для этого необходимо установить дополнительно приложение
[`django-vkontakte-groups`](http://github.com/ramusus/django-vkontakte-groups/) и добавить его в `INSTALLED_APPS`

    >>> from vkontakte_groups.models import Group
    >>> group = Group.remote.fetch(ids=[16297716])[0]
    >>> Post.remote.fetch_group_wall(group=group)
    [<Post: ...>, <Post: ...>, <Post: ...>, '...(remaining elements truncated)...']

### Получение комментариев сообщения со стены группы через менеджер

Для этого необходимо установить дополнительно приложение
[`django-vkontakte-users`](http://github.com/ramusus/django-vkontakte-users/) и добавить его в `INSTALLED_APPS`

    >>> from vkontakte_users.models import User
    >>> user = User.remote.fetch(ids=[1])[0]
    >>> post = user.wall_posts.all()[0]
    >>> Comment.remote.fetch_user_post(post=post)
    [<Comment: ...>, <Comment: ...>, <Comment: ...>, '...(remaining elements truncated)...']

### Получение комментариев сообщения со стены группы через менеджер

Для этого необходимо установить дополнительно приложение
[`django-vkontakte-groups`](http://github.com/ramusus/django-vkontakte-groups/) и добавить его в `INSTALLED_APPS`

    >>> from vkontakte_groups.models import Group
    >>> group = Group.remote.fetch(ids=[16297716])[0]
    >>> post = group.wall_posts.all()[0]
    >>> Comment.remote.fetch_group_post(post=post)
    [<Comment: ...>, <Comment: ...>, <Comment: ...>, '...(remaining elements truncated)...']