from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.forms import fields
from django.core.cache import cache

from posts.models import Post, Group, Follow

User = get_user_model()


class TaskPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create_user(username='author')
        cls.user = User.objects.create_user(username='User')
        cls.unfollow = User.objects.create_user(username='StasBasov')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug-test',
            description='Тестовое описание группы',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст поста',
            author=cls.user_author,
            group=cls.group,
        )

    def setUp(self):

        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_author = Client()
        self.authorized_author.force_login(self.user_author)
        self.unfollowing_client = Client()
        self.unfollowing_client.force_login(self.unfollow)

    def test_pages_uses_correct_template(self):
        """URL-фдрес использует соответствующий шаблон."""
        template_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': self.group.slug}): (
                'posts/group_list.html'
            ),
            reverse('posts:profile', kwargs={'username': self.user}): (
                'posts/profile.html'
            ),
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}): (
                'posts/post_detail.html'
            ),
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}): (
                'posts/create_post.html'
            ),
            reverse('posts:post_create'): 'posts/create_post.html',
        }

        for reverse_name, template in template_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_post_detail_pages_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
        )
        self.assertEqual(response.context['post'].text, self.post.text)
        self.assertEqual(response.context['post'].author, self.post.author)
        self.assertEqual(response.context['post'].group, self.post.group)

    def test_post_list_page_show_correct_context(self):
        """Шаблон post_list сформирован с правильным контекстом."""
        response = self.authorized_author.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug}))
        first_object = response.context['page_obj'][0]
        object_group = response.context['group']
        self.assertEqual(object_group.title, self.group.title)
        self.assertEqual(object_group.slug, self.group.slug)
        self.assertEqual(object_group.description, self.group.description)
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.author, self.post.author)
        self.assertEqual(first_object.group, self.post.group)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_author.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.author, self.post.author)
        self.assertEqual(first_object.group, self.post.group)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_author.get(
            reverse('posts:profile', kwargs={'username': self.post.author}))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.author, self.post.author)
        self.assertEqual(first_object.group, self.post.group)
        self.assertEqual(
            response.context['author'].username, self.user_author.username)

    def test_home_page_show_correct_context(self):
        """Шаблон create сформирован с правильным контекстом."""
        template = [
            reverse('posts:post_create'),
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
        ]
        form_fields = {
            'text': fields.CharField,
            'group': fields.ChoiceField,
        }
        for adress in template:
            with self.subTest(adress=adress):
                response = self.authorized_author.get(adress)
                for value, expected in form_fields.items():
                    with self.subTest(value=value):
                        form_field = response.context.get(
                            'form').fields.get(value)
                        self.assertIsInstance(form_field, expected)

    def test_context_edit_is_edit(self):
        response = self.authorized_author.get(reverse(
            'posts:post_edit', kwargs={'post_id': self.post.id}))
        self.assertTrue(response.context['is_edit'])

    def test_post_context_group(self):
        newgroup = Group.objects.create(
            title='Новая тестовая группа',
            slug='new-slug-test',
            description='Тестовое описание группы',
        )
        template = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': newgroup.slug}),
            reverse('posts:profile', kwargs={'username': self.user_author}),
        )
        newpost = Post.objects.create(
            text='Новый тестовый текст поста',
            author=self.user_author,
            group=newgroup,
        )
        for adress in template:
            with self.subTest(adress=adress):
                response = self.authorized_author.get(adress)
                self.assertIn(newpost, response.context['page_obj'])
        response = self.authorized_author.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug}))
        self.assertNotIn(newpost, response.context['page_obj'])

    def test_cache_index(self):
        post = Post.objects.create(
            text='Новый тестовый текст поста',
            author=self.user_author,
            group=self.group,
        )
        response = self.authorized_author.get(reverse('posts:index'))
        cache_1 = response.content
        post.delete()
        response = self.authorized_author.get(reverse('posts:index'))
        self.assertEqual(response.content, cache_1)
        cache.clear()
        response = self.authorized_author.get(reverse('posts:index'))
        self.assertNotEqual(response.content, cache_1)

    def test_authorized_user_follow(self):
        response = self.authorized_client.get(reverse('posts:follow_index'))
        context = len(response.context['page_obj'])
        response = self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.user_author}
        ))
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), context + 1)
        response = self.authorized_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.user_author}
        ))
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), context)

    def test_unfollow_client(self):
        response = self.authorized_client.get(reverse('posts:follow_index'))
        context_auth = len(response.context['page_obj'])
        response = self.unfollowing_client.get(reverse('posts:follow_index'))
        context_unfollow = len(response.context['page_obj'])
        Follow.objects.create(user=self.user, author=self.user_author)
        Post.objects.create(
            text='Новый тестовый текст поста',
            author=self.user_author,
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), context_auth + 2)
        response = self.unfollowing_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), context_unfollow)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Petya')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание'
        )
        for i in range(0, 15):
            cls.post = Post.objects.create(
                author=cls.user,
                text='Тестовый пост',
                group=cls.group,
            )
        cls.template = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': cls.group.slug}),
            reverse('posts:profile', kwargs={'username': cls.user}),
        )

    def test_first_page_contains_ten_records(self):
        for adress in self.template:
            with self.subTest(adress=adress):
                response = self.client.get(adress)
                self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records(self):
        for adress in self.template:
            with self.subTest(adress=adress):
                response = self.client.get(adress + '?page=2')
                self.assertEqual(len(response.context['page_obj']), 5)
