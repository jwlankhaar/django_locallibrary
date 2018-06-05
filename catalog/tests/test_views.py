from django.contrib.auth.models import User, Permission
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

import datetime

from catalog.models import Author, BookInstance, Book, Genre, Language
from catalog.forms import RenewBookForm


class AuthorListViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Create 13 authors for pagination tests.
        num_of_authors = 13
        for author_num in range(num_of_authors):
            Author.objects.create(
                first_name='Christian %d' % author_num,
                last_name='Surname %d' % author_num,
            )

    def test_view_url_exists_at_desired_location(self):
        resp = self.client.get('/catalog/authors/')
        self.assertEqual(resp.status_code, 200)

    def test_view_url_accessible_by_name(self):
        resp = self.client.get(reverse('authors'))
        self.assertEqual(resp.status_code, 200)

    def test_view_uses_correct_template(self):
        resp = self.client.get(reverse('authors'))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'catalog/author_list.html')

    def test_pagination_is_ten(self):
        resp = self.client.get(reverse('authors'))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('is_paginated' in resp.context)
        self.assertTrue(resp.context['is_paginated'])
        self.assertEqual(len(resp.context['author_list']), 10)

    def test_lists_all_users(self):
        # Get second page and confirm it has (exactly) 3 remaining items.
        resp = self.client.get(reverse('authors') + '?page=2')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('is_paginated' in resp.context)
        self.assertTrue(resp.context['is_paginated'])
        self.assertEqual(len(resp.context['author_list']), 3)

    def test_authors_ordered_by_last_name_first_name(self):
        
        # Assign names to authors.
        num_of_authors = 5
        author_names = [
            ('Xantipe', 'Xerox'),
            ('Mirjam', 'Lankhaar'),
            ('Yale', 'Yelling'),
            ('Alicia', 'Arnold'),
            ('Jan-Willem', 'Lankhaar')
        ]
        for auth in Author.objects.all()[0:num_of_authors]:
            first_name, last_name = author_names.pop()
            auth.first_name = first_name
            auth.last_name = last_name
            auth.save()
            
        # List authors.
        resp = self.client.get(reverse('authors'))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('author_list' in resp.context)

        # Test alphabetical ordering.
        prev_auth_first_name = None
        prev_auth_last_name = None
        for auth in resp.context['author_list']:
            if prev_auth_first_name and prev_auth_last_name:
                self.assertTrue(auth.last_name >= prev_auth_last_name)
                if auth.last_name == prev_auth_last_name:
                    self.assertTrue(auth.first_name >= prev_auth_first_name)
            else:
                prev_auth_first_name = auth.first_name
                prev_auth_last_name = auth.last_name
                

class LoanedBooksByUserListViewTest(TestCase):

    def setUp(self):
        
        # Create two users.
        test_user1 = User.objects.create_user(
            username='testuser1',
            password='12345'
        )
        test_user1.save()
        test_user2 = User.objects.create_user(
            username='testuser2',
            password='12345')
        test_user2.save()

        # Create a book.
        test_author = Author.objects.create(
            first_name='John',
            last_name='Smith')
        test_genre = Genre.objects.create(name='Fantasy')
        test_language = Language.objects.create(name='English')
        test_book = Book.objects.create(
            title='Book Title',
            summary='My book summary',
            isbn='ABCDEFGHIJKLM',
            author=test_author,
            language=test_language)

        # Create genre as a post-step.
        genre_objects_for_book = Genre.objects.all()
        test_book.genre.set(genre_objects_for_book) # Direct assignment of 
                                                    # many-to-many types not 
                                                    # allowed.
        test_book.save()

        # Create 30 book instance objects.
        num_of_book_copies = 30
        for book_copy in range(num_of_book_copies):
            return_date = (timezone.now()
                           + datetime.timedelta(days=book_copy % 5))
            if book_copy % 2:
                the_borrower = test_user1
            else:
                the_borrower = test_user2
            status = 'm'
            BookInstance.objects.create(
                book=test_book,
                imprint='Unlikely Imprint, 2016',
                due_back=return_date,
                borrower=the_borrower,
                status=status)

    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(reverse('my-borrowed'))
        self.assertRedirects(resp, '/accounts/login/?next=/catalog/mybooks/')

    def test_logged_in_uses_correct_template(self):
        login = self.client.login(
            username='testuser1',
            password='12345')
        resp = self.client.get(reverse('my-borrowed'))

        # Check whether user is logged in we get a 'success' response .
        self.assertEqual(str(resp.context['user']), 'testuser1')
        self.assertEqual(resp.status_code, 200)

        # Check template.
        self.assertTemplateUsed(
            resp, 'catalog/bookinstance_list_borrowed_user.html')

    def test_only_borrowed_books_in_list(self):
        login = self.client.login(
            username='testuser1',
            password='12345')
        resp = self.client.get(reverse('my-borrowed'))

        # Check whether user is logged in we get a 'success' response .
        self.assertEqual(str(resp.context['user']), 'testuser1')
        self.assertEqual(resp.status_code, 200)

        # Check that initially we don't have any books in list (none on loan).
        self.assertTrue('bookinstance_list' in resp.context)
        self.assertEqual(len(resp.context['bookinstance_list']), 0)

        # Now, change all books to be on loan.
        get_ten_books = BookInstance.objects.all()[:10]
        for copy in get_ten_books:
            copy.status = 'o'
            copy.save()

        # Check that we have borrowed books in the list now.
        resp = self.client.get(reverse('my-borrowed'))
        self.assertEqual(str(resp.context['user']), 'testuser1')
        self.assertEqual(resp.status_code, 200)

        self.assertTrue('bookinstance_list' in resp.context)

        # Confirm all books belong to testuser1 and are on loan.
        for bookitem in resp.context['bookinstance_list']:
            self.assertEqual(resp.context['user'], bookitem.borrower)
            self.assertEqual(bookitem.status, 'o')

    def test_pages_ordered_by_due_date(self):
        
        # Change all books to be on loan.
        for copy in BookInstance.objects.all():
            copy.status = 'o'
            copy.save()

        login = self.client.login(username='testuser1', password='12345')
        resp = self.client.get(reverse('my-borrowed'))
        self.assertEqual(str(resp.context['user']), 'testuser1')
        self.assertEqual(resp.status_code, 200)

        # Confirm that of the items, only 10 are displayed due to pagination.
        self.assertEqual(len(resp.context['bookinstance_list']), 10)

        last_date = 0
        for copy in resp.context['bookinstance_list']:
            if last_date == 0:
                last_date = copy.due_back
            else:
                self.assertTrue(last_date <= copy.due_back)
        
    def test_myborrowed_paginated(self):
        
        # Change all books to be on loan.
        for copy in BookInstance.objects.all():
            copy.status = 'o'
            copy.save()
        
        login = self.client.login(username='testuser1', password='12345')
        resp = self.client.get(reverse('my-borrowed'))
        self.assertEqual(str(resp.context['user']), 'testuser1')
        self.assertEqual(resp.status_code, 200)

        # Check first page (should contain 10 items).
        resp = self.client.get(reverse('my-borrowed'))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('is_paginated' in resp.context)
        self.assertTrue(resp.context['is_paginated'])
        self.assertEqual(len(resp.context['bookinstance_list']), 10)

        # Check next page (should contain 5 items).
        resp = self.client.get(reverse('my-borrowed') + '?page=2')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(len(resp.context['bookinstance_list']), 5)
        
    def test_only_borrowed_books_in_list(self):
        
        # Log in and request user's borrowed list.
        login = self.client.login(
            username='testuser1',
            password='12345')
        resp = self.client.get(reverse('my-borrowed'))

        # Check whether user is logged in.
        self.assertEqual(str(resp.context['user']), 'testuser1')
        self.assertEqual(resp.status_code, 200)

        # Check that, initially, we don't have any books on loan.
        self.assertTrue('bookinstance_list' in resp.context)
        self.assertEqual(len(resp.context['bookinstance_list']), 0)

        # Change 10 books to be on loan.
        bookinstances_to_borrow = BookInstance.objects.all()[:10]
        for inst in bookinstances_to_borrow:
            inst.status = 'o'
            inst.save()
        
        # Check that, now, we have books on loan.
        resp = self.client.get(reverse('my-borrowed'))
        self.assertEqual(str(resp.context['user']), 'testuser1')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('bookinstance_list' in resp.context)
        for bookitem in resp.context['bookinstance_list']:
            self.assertEqual(bookitem.borrower, resp.context['user'])
            self.assertEqual(bookitem.status, 'o')

    def test_bookinstances_ordered_by_due_date(self):
        
        # Log in and request user's borrowed list.
        login = self.client.login(username='testuser1', password='12345')
        resp = self.client.get(reverse('my-borrowed'))

        # Check whether user is logged in.
        self.assertEqual(str(resp.context['user']), 'testuser1')
        self.assertEqual(resp.status_code, 200)

        # Check that, initially, we don't have any books on loan.
        self.assertTrue('bookinstance_list' in resp.context)
        self.assertEqual(len(resp.context['bookinstance_list']), 0)

        # Change 20 books to be on loan with increasing due dates.
        due_date = datetime.datetime.today() - datetime.timedelta(weeks=-2)
        bookinstances_to_borrow = BookInstance.objects.all()[:10]
        for inst in bookinstances_to_borrow:
            inst.status = 'o'
            inst.due_date = due_date
            inst.save()
            due_date += datetime.timedelta(days=3)

        # Check that we have 10 books on loan.
        resp = self.client.get(reverse('my-borrowed'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(str(resp.context['user']), 'testuser1')
        self.assertTrue('bookinstance_list' in resp.context)
        self.assertEqual(len(resp.context['bookinstance_list']), 5)

        # Check whether items are ordered by ascending due date.
        previous_due = None
        for bookinst in resp.context['bookinstance_list']:
            if previous_due:
                self.assertTrue(bookinst.due_back >= previous_due)
            previous_due = bookinst.due_back


class RenewBookInstancesLibrarianTest(TestCase):
    
    def setUp(self):
        
        # Create users.
        test_user1 = User.objects.create_user(
            username='testuser1', password='12345')
        test_user1.save()
        test_user2 = User.objects.create_user(
            username='testuser2', password='12345')
        test_user2.save()
        permission = Permission.objects.get(name='Set book as returned')
        test_user2.user_permissions.add(permission)
        test_user2.save()

        # Create a book.
        test_author = Author.objects.create(
            first_name='John', 
            last_name='Doe')
        test_genre = Genre.objects.create(name='Fantasy')
        test_language = Language.objects.create(name='English')
        test_book = Book.objects.create(
            title='Book Title',
            summary='My book summary',
            isbn='9876543210ABC',
            author=test_author,
            language=test_language)
        
        # Create genre as a post-step. Direct many-to-many assignment not 
        # allowed.
        genre_objects_for_book = Genre.objects.all()
        test_book.genre.set(genre_objects_for_book)
        test_book.save()

        # Create a BookInstance object for test_user1.
        return_date = datetime.date.today() + datetime.timedelta(days=5)
        self.test_bookinstance1 = BookInstance.objects.create(
            book=test_book,
            imprint='Unlikely Imprint, 2018',
            due_back=return_date,
            borrower=test_user1,
            status='o')

        return_date = datetime.date.today() + datetime.timedelta(days=5)
        self.test_bookinstance2 = BookInstance.objects.create(
            book=test_book,
            imprint='Unlikely Imprint, 2018',
            due_back=return_date,
            borrower=test_user2,
            status='o')
    
    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(
            reverse(
                'renew-bookinstance-librarian',
                kwargs={'pk': self.test_bookinstance1.pk}))

        # Manually check redirect (can't use assertRedirect, because the
        # redirect URL is unpredictable).
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp.url.startswith('/accounts/login/'))

    def test_redirect_if_logged_in_but_not_correct_permission(self):
        login = self.client.login(
            username='testuser1', password='12345')
        resp = self.client.get(
            reverse(
                'renew-bookinstance-librarian',
                kwargs={'pk':self.test_bookinstance1.pk}))
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp.url.startswith('/accounts/login/'))

    def test_logged_in_with_permissions_borrowed_book(self):
        login = self.client.login(
            username='testuser2', password='12345')
        resp = self.client.get(
            reverse(
                'renew-bookinstance-librarian',
                kwargs={'pk': self.test_bookinstance2.pk}))
                
        # Check whether it lets the user log in.
        self.assertEqual(resp.status_code, 200)

    def test_logged_in_with_permissions_another_users_borrowed_book(self):
        login = self.client.login(
            username='testuser2', password='12345'
        )
        resp = self.client.get(
            reverse(
                'renew-bookinstance-librarian',
                kwargs={'pk': self.test_bookinstance1.pk}
            )
        )
        # test_user2 is a librarian, so should be able to renew any user's 
        # book.
        self.assertEqual(resp.status_code, 200)

    def test_HTTP404_for_invalid_book_if_logged_in(self):
        import uuid
        test_uuid = uuid.uuid4()
        login = self.client.login(
            username='testuser2', password='12345')
        resp = self.client.get(
            reverse(
                'renew-bookinstance-librarian',
                kwargs={'pk': test_uuid}))
        self.assertEqual(resp.status_code, 404)

    def test_uses_correct_template(self):
        login = self.client.login(
            username='testuser2', password='12345')
        resp = self.client.get(
            reverse('renew-bookinstance-librarian',
            kwargs={'pk': self.test_bookinstance1.pk}))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(
            resp,
            'catalog/bookinstance_renew_librarian.html')

    def test_logged_in_uses_correct_template(self):
        login = self.client.login(
            username='testuser1',
            password='12345')
        resp = self.client.get(reverse('my-borrowed'))

        # Check whether user is logged in.
        self.assertEqual(str(resp.context['user']), 'testuser1')
        self.assertEqual(resp.status_code, 200)

        # Check whether correct template was used.
        self.assertTemplateUsed(
            resp, 'catalog/bookinstance_list_borrowed_user.html')

    def test_form_renewal_date_initially_has_three_weeks_in_future(self):
        login = self.client.login(
            username='testuser2', password='12345')
        resp = self.client.get(
            reverse(
                'renew-bookinstance-librarian',
                kwargs={'pk': self.test_bookinstance1.pk}))
        self.assertEqual(resp.status_code, 200)
        date_3_weeks_in_future = (datetime.date.today()
                                  + datetime.timedelta(weeks=3))
        self.assertEqual(
            resp.context['form'].initial['renewal_date'],
            date_3_weeks_in_future)

    def test_redirects_to_all_borrowed_books_list_on_success(self):
        login = self.client.login(
            username='testuser2', password='12345')
        valid_date_in_future = (datetime.date.today()
                                + datetime.timedelta(weeks=2))
        resp = self.client.post(
            reverse(
                'renew-bookinstance-librarian',
                kwargs={'pk': self.test_bookinstance1.pk}),
            {'renewal_date': valid_date_in_future})
        self.assertRedirects(resp, reverse('all-borrowed'))

    def test_form_invalid_renewal_date_past(self):
        login = self.client.login(
            username='testuser2', password='12345')
        date_in_past = datetime.date.today() - datetime.timedelta(weeks=1)
        resp = self.client.post(
            reverse(
                'renew-bookinstance-librarian',
                kwargs={'pk': self.test_bookinstance1.pk}),
            {'renewal_date': date_in_past})
        self.assertEqual(resp.status_code, 200)
        self.assertFormError(resp, 'form', 'renewal_date',
            'Invalid date - renewal in the past')

    def test_form_invalid_renewal_date_future(self):
        login = self.client.login(
            username='testuser2', password='12345')
        date_in_future = datetime.date.today() + datetime.timedelta(weeks=5)
        resp = self.client.post(
            reverse(
                'renew-bookinstance-librarian',
                kwargs={'pk': self.test_bookinstance1.pk}),
            {'renewal_date': date_in_future})
        self.assertEqual(resp.status_code, 200)
        self.assertFormError(resp, 'form', 'renewal_date',
            'Invalid date - renewal more than 4 weeks ahead')


class AuthorCreateViewTest(TestCase):
    
    def setUp(self):

        # Create users.
        test_user_noperm = User.objects.create_user(
            username='test_user_noperm', password='12345')
        test_user_noperm.save()
        test_user_perm = User.objects.create_user(
            username='test_user_perm', password='12345')
        test_user_perm.save()
        permission = Permission.objects.get(
            name='Create, update or delete author details')
        test_user_perm.user_permissions.add(permission)
        test_user_perm.save()

        # Create some authors.
        num_of_authors = 10
        for i in range(num_of_authors):
            Author.objects.create()
    
    def test_redirect_user_not_logged_in(self):
        resp = self.client.get(reverse('author-create'))
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(
            resp,
            '/accounts/login/?next=/catalog/author/create/')

    def test_redirect_user_logged_in_wrong_permission(self):
        login = self.client.login(
            username='test_user_noperm', password='12345')
        resp = self.client.get(reverse('author-create'))
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(
            resp, '/accounts/login/?next=/catalog/author/create/')

    def test_view_url_accessible_by_name_user_logged_in_with_permissions(self):
        login = self.client.login(
            username='test_user_perm', password='12345')
        resp = self.client.get(reverse('author-create'))
        self.assertEqual(resp.status_code, 200)

    def test_initial_date_of_death_2099_12_31(self):
        login = self.client.login(username='test_user_perm', password='12345')
        resp = self.client.get(reverse('author-create'))
        self.assertEqual(resp.status_code, 200)
        expected_date_of_death = '12/31/2099'
        self.assertEqual(
            resp.context['form'].initial['date_of_death'],
            expected_date_of_death)

    def test_correct_template_used(self):
        login = self.client.login(username='test_user_perm', password='12345')
        resp = self.client.get(reverse('author-create'))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'catalog/author_form.html')
    
    def test_correct_redirect_on_success(self):
        import re

        login = self.client.login(username='test_user_perm', password='12345')
        first_name = 'Mirjam'
        last_name = 'Lankhaar'
        date_of_birth = '05/16/1977'
        date_of_death = ''
        resp = self.client.post(
            reverse('author-create'),
            {
                'first_name': first_name,
                'last_name': last_name,
                'date_of_birth': date_of_birth,
                'date_of_death': date_of_death
            })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(re.search('author/\d+/', resp.url))

