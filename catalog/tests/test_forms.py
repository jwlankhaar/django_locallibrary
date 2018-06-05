from django.test import TestCase
from django.utils import timezone

import datetime

from catalog.forms import RenewBookForm


# Create your tests here.
class RenewBookFormTest(TestCase):

    def test_renewal_date_label(self):
        form = RenewBookForm()
        renewal_date_label = form.fields['renewal_date'].label
        self.assertTrue(
            renewal_date_label == None or
            renewal_date_label == 'renewal date'
        )

    def test_renewal_date_help_text(self):
        form = RenewBookForm()
        help_text = form.fields['renewal_date'].help_text
        expected_text = 'Enter a date between now and 4 weeks (default 3).'
        self.assertEquals(help_text, expected_text)

    def test_renewal_date_in_past(self):
        form = RenewBookForm()
        date = datetime.date.today() - datetime.timedelta(days=1)
        form_data = {'renewal_date': date}
        form = RenewBookForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_renewal_date_too_far_in_future(self):
        date = (datetime.date.today()
                + datetime.timedelta(weeks=4)
                + datetime.timedelta(days=1))
        form_data = {'renewal_date': date}
        form = RenewBookForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_renewal_date_today(self):
        date = datetime.date.today()
        form_data = {'renewal_date': date}
        form = RenewBookForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_renewal_date_max(self):
        date = datetime.date.today() + datetime.timedelta(weeks=4)
        form_data = {'renewal_date': date}
        form = RenewBookForm(data=form_data)
        self.assertTrue(form.is_valid())

    