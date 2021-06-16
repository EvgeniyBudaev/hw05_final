from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Group, Post

User = get_user_model()


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B')
        cls.author = User.objects.create(username='Evgeniy')
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='test_slug',
            description='Тестовое описание группы'
        )
        cls.test_user = User.objects.create(
            username='test_user'
        )
        cls.test_group = Group.objects.create(
            title='Тестовая группа',
            slug='test-group',
            description='test-group',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            group=cls.group
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        self.guest_client = Client()
        self.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=PostFormTests.small_gif,
            content_type='image/gif'
        )

    def test_post_form_create_new_post(self):
        """Форма создаёт пост в базе и перенаправляет пользователя
        на главную страницу."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост из формы',
            'group': self.group.id,
            'image': self.uploaded
        }
        new_text_form = 'Тестовый пост из формы'
        response = self.authorized_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(Post.objects.filter(
            text=new_text_form,
            group=self.group.id,
            author=self.author
        ).exists())
        last_object = Post.objects.filter().order_by('-id')[0]
        self.assertEqual(last_object.text, form_data['text'])
        self.assertRedirects(response, reverse('index'))

    def test_edit_post_in_form(self):
        """проверка редактирования поста."""
        new_text = 'Новый текст'
        form_data = {
            'text': new_text,
            'group': self.group.id,
            'image': self.uploaded
        }
        self.authorized_client.post(
            reverse('post_edit',
                    kwargs={'username': self.author.username,
                            'post_id': self.post.id}),
            data=form_data
        )
        response = self.authorized_client.get(
            reverse('post',
                    kwargs={'username': self.author.username,
                            'post_id': self.post.id})
        )
        self.assertEqual(response.context['post'].text, new_text)
        self.assertTrue(Post.objects.filter(
            text=new_text,
            group=self.group.id
        ).exists())

    def test_create_post_guest(self):
        """Проверка создания поста неавторизованным пользователем."""
        form_data = {
            'text': 'Гость пытается создать новую запись в группе',
            'group': self.test_group.id,
        }

        posts_count = Post.objects.count()

        response = self.guest_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(response.status_code, 200)

    def test_edit_post_not_author(self):
        """Проверка на то, что авторизованный пользователь не может
        отредактировать чужой пост. """
        form_data_edit = {
            'text': 'Исправленный не автором текст записи',
            'group': self.test_group.id,
        }
        test_post = Post.objects.create(
            text='Тестовый текст записи',
            author=self.test_user,
            group=self.test_group,
        )

        not_author_user = User.objects.create(
            username='not_author'
        )
        not_author_client = Client()
        not_author_client.force_login(not_author_user)

        kwargs = {'username': 'test_user', 'post_id': test_post.id}

        response = not_author_client.post(
            reverse('post_edit', kwargs=kwargs),
            data=form_data_edit,
            follow=True
        )
        test_post.refresh_from_db()
        self.assertNotEqual(test_post.text, form_data_edit['text'])
        self.assertEqual(test_post.group, self.test_group)
        self.assertEqual(test_post.author, self.test_user)
        self.assertEqual(response.status_code, 200)
