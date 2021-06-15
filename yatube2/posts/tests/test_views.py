from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from posts.models import Post, Group, Comment


User = get_user_model()


class PostsPagesTests(TestCase):
    uploaded = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        small_jpg = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.jpg',
            content=small_jpg,
            content_type='image/jpg'
        )
        cls.user = User.objects.create(username='test_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            description='Описание',
            slug='test-slug',
        )

        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            image=PostsPagesTests.uploaded
        )

        cls.post2 = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group,
            image=PostsPagesTests.uploaded
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.form_fields_new_post = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField
        }
        self.pages_with_posts = [
            reverse('index'),
            reverse('group_posts', kwargs={'slug': 'test-slug'})
        ]

    # Проверяем используемые шаблоны
    def test_pages_use_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = {
            'posts/index.html': reverse('index'),
            'posts/new_post.html': reverse('new_post'),
            'posts/group.html': reverse('group_posts',
                                        kwargs={'slug': 'test-slug'}),
        }
        for template, reverse_name in templates_page_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    # Проверка словаря контекста главной страницы
    def test_home_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        cache.clear()
        response = self.guest_client.get(reverse('index'))
        self.assertEqual(response.context.get('page').object_list[-1],
                         self.post)

    # Проверка словаря context страницы group
    # и созданный пост в этой группе
    def test_group_page_show_correct_context(self):
        """Шаблон group сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse(
            'group_posts', kwargs={'slug': 'test-slug'}
        ))
        self.assertEqual(response.context['group'], self.group)
        self.assertEqual(response.context.get('page').object_list[-1],
                         self.post2)

    # Проверка словаря context и страницы создания поста
    def test_new_page_shows_context(self):
        """Шаблон new_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('new_post'))
        for value, expected in self.form_fields_new_post.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    # Проверка на отсутствие на страницы group другой группы созданного поста
    def test_group_pages_not_show_new_post(self):
        """Шаблон group не содержит искомый контекст."""
        response = self.authorized_client.get(
            reverse('group_posts', kwargs={'slug': 'test-slug'}))
        self.assertTrue(self.post not in response.context['page'])

    def test_page_not_found(self):
        """Сервер возвращает код 404, если страница не найдена."""
        response_page_not_found = self.guest_client.get('/tests_url/')
        self.assertEqual(response_page_not_found.status_code, 404)

    def test_cache_index(self):
        """Проверяем создается ли кеш главной страницы"""
        client = Client()
        user = User.objects.create_user(username='dmitriy',
                                        password='novikov')
        client.force_login(user)
        cache.clear()
        client.post(reverse('new_post'), {'author': user,
                                          'text': 'test_cache'}, follow=True)
        Post.objects.get(author=user)
        x = cache.get('index_page')
        x = cache._cache.keys()
        self.assertIn('index_page', f'{x}')


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Test User')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        for count in range(15):
            cls.post = Post.objects.create(
                text=f'Тестовый пост номер {count}',
                author=cls.user)

    def test_first_page_contains_ten_records(self):
        """Работа пагинатора на первой странице с 10-тью записями"""
        response = self.authorized_client.get(reverse('index'))
        self.assertEqual(len(response.context.get('page').object_list), 10)

    def test_second_page_contains_five_records(self):
        """Работа пагинатора на второй странице с 5-тью записями"""
        response = self.authorized_client.get(
            reverse('index') + '?page=2'
        )
        self.assertEqual(len(response.context.get('page').object_list), 5)


class TestComment(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Jack')

        cls.post = Post.objects.create(text='Просто текст', author=cls.user)

    def test_authorized_user_comments_posts(self):
        """Проверка на добавление комментария авторизованным юзером."""
        self.client.force_login(TestComment.user)

        self.client.post(
            reverse(
                'add_comment',
                kwargs={
                    'username': TestComment.user.username,
                    'post_id': TestComment.post.id}),
                data={'text': 'Комментарий авторизированного пользователя'},
                follow=True)

        self.assertTrue(
            Comment.objects.filter(
                text='Комментарий авторизированного пользователя',
                post_id=TestComment.post.id).exists())

    def test_comment_notauthorized(self):
        """Проверка на добавление комментария не авторизованным юзером."""
        self.client.post(
            reverse(
                'add_comment',
                kwargs={
                    'username': TestComment.user.username,
                    'post_id': TestComment.post.id}),
                data={'text': 'Комментарий неавторизированного пользователя'},
                follow=True)

        self.assertFalse(
            Comment.objects.filter(
                text='Комментарий неавторизированного пользователя',
                post_id=TestComment.post.id).exists())
