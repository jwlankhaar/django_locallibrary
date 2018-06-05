from django.test import TestCase

from catalog.models import Author, Book, BookInstance, Genre
import datetime

# Create your tests here.
class AuthorModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Set up non-modified objects used by all test methods.
        Author.objects.create(first_name='Big', last_name='Bob')

    def test_first_name(self):
        author = Author.objects.get(id=1)
        field_label = author._meta.get_field('first_name').verbose_name
        self.assertEqual(field_label, 'first name')

    def test_date_of_death_label(self):
        author = Author.objects.get(id=1)
        field_label = author._meta.get_field('date_of_death').verbose_name
        self.assertEqual(field_label, 'died')

    def test_first_name_max_lengthv(self):
        author = Author.objects.get(id=1)
        max_length = author._meta.get_field('first_name').max_length
        self.assertEquals(max_length, 100)

    def test_object_name_is_last_name_comma_first_name(self):
        author = Author.objects.get(id=1)
        expected_object_name = '%s, %s' % (author.last_name, author.first_name)
        self.assertEquals(expected_object_name, str(author))

    def test_get_absolute_url(self):
        author = Author.objects.get(id=1)
        # This will also fail if the urlconf is not defined.
        self.assertEquals(author.get_absolute_url(), '/catalog/author/1/')


class BookInstanceModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        BookInstance.objects.create(
            book=Book.objects.create(),
            due_back=datetime.datetime.today()
                     + datetime.timedelta(weeks=-1)
        )
        BookInstance.objects.create(
            book=Book.objects.create(),
            due_back=datetime.datetime.today()
                     + datetime.timedelta(weeks=+1)
        )

    def test_default_loan_status(self):
        book_inst = BookInstance.objects.first()
        default_status = book_inst.status
        expected_status = 'm'
        self.assertEquals(default_status, expected_status)

    def test_is_overdue(self):
        book_inst = BookInstance.objects.first()
        overdue_status = book_inst.is_overdue
        self.assertTrue(overdue_status)

    def test_is_not_overdue(self):
        book_inst = BookInstance.objects.last()
        overdue_status = book_inst.is_overdue
        self.assertFalse(overdue_status)


class GenreModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        Genre.objects.create(name='TestGenre')

    def test_name_field_max_length(self):
        genre = Genre.objects.first()
        max_length = genre._meta.get_field('name').max_length
        expected_length = 200
        self.assertEquals(max_length, expected_length)