from django.test import TestCase
from django.contrib.auth import get_user_model

from posts.models import Group, Post

User = get_user_model()


class GroupModelTest(TestCase):
    group = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.group = Group.objects.create(
            title='Заголовок тестового сообщества',
            description='Тестовый текст',
            slug='test-task'
        )
        cls.group = GroupModelTest.group

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        field_verboses = {
            'title': 'Название сообщества',
            'description': 'Описание',
            'slug': 'Адрес'
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    GroupModelTest.group._meta.get_field(field).verbose_name,
                    expected_value)

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        field_help_texts = {
            'slug': ('Задайте уникальный URL адрес названию '
                     'сообщества')
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    GroupModelTest.group._meta.get_field(field).help_text,
                    expected_value)

    def test_object_name_is_title_field(self):
        """В поле __str__  объекта group записано значение поля group.title."""
        expected_object_name = GroupModelTest.group.title
        self.assertEqual(expected_object_name, str(GroupModelTest.group))


class PostModelTest(TestCase):
    group = None
    post = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create(username='author', )
        cls.group = Group.objects.create(title='Тестовая группа')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group
        )

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        field_verboses = {
            'group': 'Сообщество',
            'text': 'Текст поста',
            'author': 'Автор'
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    PostModelTest.post._meta.get_field(field).verbose_name,
                    expected_value)

    def test_object_name_is_text_field(self):
        """В поле __str__  объекта post записано значение поля post.text."""
        post = PostModelTest.post
        expected_object_name = post.text[:15]
        self.assertEqual(expected_object_name, str(post))

    def test_group_title_str(self):
        """Название группы совпадает"""
        group = PostModelTest.group
        title = str(group)
        self.assertEqual(title, group.title)
