from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post, Comment

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост длиной больше 15 симловов',
        )
        cls.comment = Comment.objects.create(
            text='Пробный тест длинной больше 15 символов',
            author=cls.user,
            post=cls.post
        )

    def test_post_models_have_correct_object_names(self):
        post_value = str(self.post)
        expected_value = self.post.text[:15]
        self.assertEqual(post_value, expected_value)

    def test_group_models_have_correct_object_names(self):
        group_value = str(self.group)
        expected_value = self.group.title
        self.assertEqual(group_value, expected_value)

    def test_comment_models_have_correct_object_names(self):
        comment_value = str(self.comment)
        expected_value = self.comment.text[:15]
        self.assertEqual(comment_value, expected_value)
