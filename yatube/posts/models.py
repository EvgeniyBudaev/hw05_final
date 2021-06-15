from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200,
                             verbose_name="Название сообщества")
    slug = models.SlugField(max_length=200, unique=True, verbose_name="Адрес",
                            help_text='Задайте уникальный URL адрес названию '
                                      'сообщества')
    description = models.TextField(null=True, blank=True,
                                   verbose_name="Описание")

    class Meta:
        ordering = ["title"]
        verbose_name = "Группу"
        verbose_name_plural = "Группы"

    def __str__(self):
        return self.title


class Post(models.Model):
    group = models.ForeignKey(Group, null=True, blank=True,
                              verbose_name="Сообщество",
                              related_name="posts",
                              on_delete=models.SET_NULL,
                              help_text='Выберите пожалуйста группу')
    text = models.TextField(verbose_name="Текст поста",
                            help_text='Введите пожалуйста текст вашего поста')
    pub_date = models.DateTimeField(auto_now_add=True,
                                    verbose_name="Дата публикации",
                                    db_index=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name="posts", verbose_name="Автор")
    image = models.ImageField(upload_to='posts/', blank=True, null=True,
                              verbose_name="Изображение",
                              help_text='Добавьте изображение к посту')

    class Meta:
        ordering = ["-pub_date"]
        verbose_name = "Пост"
        verbose_name_plural = "Посты"

    def __str__(self):
        return self.text[:15]


class Comment(models.Model):
    post = models.ForeignKey(Post,
                             on_delete=models.CASCADE,
                             related_name='comments',
                             verbose_name='Пост')
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='comments',
                               verbose_name='Автор')
    text = models.TextField(verbose_name='Текст комментария',
                            help_text='Введите пожалуйста текст вашего '
                                      'комментария')
    created = models.DateTimeField(auto_now_add=True,
                                   verbose_name='Дата комментария')

    class Meta:
        ordering = ['-created']
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return self.text


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор')
    subscribe_date = models.DateTimeField("date published",
                                          auto_now_add=True,
                                          db_index=True)

    class Meta:
        verbose_name = 'Подписчик'
        verbose_name_plural = 'Подписчики'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'], name='unique subscribers')]

    def __str__(self):
        return f'{self.user} подписан на {self.author}'


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    photo = models.ImageField(
        upload_to='users/',
        default='users/avatar.png',
        verbose_name='Аватарка',
        help_text='Добавьте аватарку')

    class Meta:
        verbose_name_plural = 'Профили пользователей'
        verbose_name = 'Профиль пользователя'

    def __str__(self):
        return self.user.username
