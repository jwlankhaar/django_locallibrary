from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, \
                                       PermissionRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views import generic
from django.views.generic.edit import CreateView, UpdateView, DeleteView

from .models import Book, Author, BookInstance, Genre
from .forms import RenewBookForm

import datetime


# Create your views here.
def index(request):
    """
    View function for home page of site.
    """

    # Generate counts of some of the main objects.
    num_books = Book.objects.all().count()
    num_instances = BookInstance.objects.all().count()

    # Available books (status = 'a').
    num_instances_available = BookInstance.objects.filter(
        status__exact='a').count()
    # The 'all()' is implied by default.
    num_authors = Author.objects.count()
    num_genres = Genre.objects.count()
    num_books_intitle_om = Book.objects.filter(title__icontains='om').count()

    # Number of visits to this view, as counted in the session variable.
    num_visits = request.session.get('num_visits', 0)
    request.session['num_visits'] = num_visits+1

    # Render the HTML template index.html with the data in the context variable.
    return render(
        request,
        'index.html',
        context={
            'num_books': num_books,
            'num_instances': num_instances,
            'num_instances_available': num_instances_available,
            'num_authors': num_authors,
            'num_genres': num_genres,
            'num_books_intitle_om': num_books_intitle_om,
            'num_visits': num_visits
        }
    )


class BookListView(generic.ListView):
    model = Book
    paginate_by = 10


class BookDetailView(generic.DetailView):
    model = Book


class AuthorListView(generic.ListView):
    model = Author
    paginate_by = 10


class AuthorDetailView(generic.DetailView):
    model = Author
    # book_list = Book.objects.filter(author=model.author)


class LoanedBooksByUserListView(LoginRequiredMixin, generic.ListView):
    """
    Generic class-based view listing books on loan to current user.
    """

    model = BookInstance
    template_name = 'catalog/bookinstance_list_borrowed_user.html'
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(
            borrower=self.request.user
        ).filter(status__exact='o').order_by('due_back')
   

class LoanedBooksListView(LoginRequiredMixin, generic.ListView):
    """
    Generic class-based view listing books on loan.
    """

    model = BookInstance
    template_name = 'catalog/bookinstance_list_borrowed_all.html'
    paginate_by = 10

    permission_required = 'catalog.can_mark_returned'

    def get_queryset(self):
        return BookInstance.objects.filter(
            status__exact='o').order_by('due_back')
           

@permission_required('catalog.can_mark_returned')
def renew_bookinstance_librarian(request, pk):
    """
    View function for renewing a specific BookInstance by librarian.
    """

    book_inst = get_object_or_404(BookInstance, pk=pk)

    # If this is a POST request then process the Form data.
    if request.method == 'POST':
        
        # Create a form instance and populate it with data from the request 
        # (binding).
        form = RenewBookForm(request.POST)

        # Check if form is valid.
        if form.is_valid():
            
            # Process the data in form.cleaned_data as required (we just write
            # it to the model due_back field).
            book_inst.due_back = form.cleaned_data['renewal_date']
            book_inst.save()

            # Redirect to a new URL.
            return HttpResponseRedirect(reverse('all-borrowed'))

    # If this is a GET (or any other method) create the default form.
    else:
        proposed_renewal_date = (datetime.date.today()
                                 + datetime.timedelta(weeks=3))
        form = RenewBookForm(
            initial={'renewal_date': proposed_renewal_date}
        )

    return render(
        request,
        'catalog/bookinstance_renew_librarian.html',
        {'form': form, 'bookinst': book_inst}
    )


class AuthorCreate(PermissionRequiredMixin, CreateView):
    model = Author
    fields = '__all__'
    initial = {'date_of_death': '12/31/2099'}
    permission_required = ('catalog.can_create_update_delete_author')


class AuthorUpdate(PermissionRequiredMixin, UpdateView):
    model = Author
    fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death']
    permission_required = ('catalog.can_create_update_delete_author')


class AuthorDelete(PermissionRequiredMixin, DeleteView):
    model = Author
    success_url = reverse_lazy('authors')
    permission_required = ('catalog.can_create_update_delete_author')


class GenreCreate(PermissionRequiredMixin, CreateView):
    model = Genre
    fields = '__all__'
    permission_required = ('catalog.can_create_update_delete_genre')


class GenreUpdate(PermissionRequiredMixin, UpdateView):
    model = Genre
    fields = '__all__'
    permission_required = ('catalog.can_create_update_delete_genre')


class GenreDelete(PermissionRequiredMixin, DeleteView):
    model = Genre
    success_url = reverse_lazy('index')
    permission_required = ('catalog.can_create_update_delete_genre')


class BookCreate(PermissionRequiredMixin, CreateView):
    model = Book
    fields = '__all__'
    permission_required = ('catalog.can_create_update_delete_book')


class BookUpdate(PermissionRequiredMixin, UpdateView):
    model = Book
    fields = '__all__'
    permission_required = ('catalog.can_create_update_delete_book')


class BookDelete(PermissionRequiredMixin, DeleteView):
    model = Book
    success_url = 'books'
    permission_required = ('catalog.can_create_update_delete_book')

