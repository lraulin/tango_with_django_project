from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from rango.forms import CategoryForm, PageForm, UserForm, UserProfileForm
from rango.models import Category, Page, UserProfile
from rango.webhose_search import run_query
from django.contrib.auth.models import User


def get_server_side_cookie(request, cookie, default_val=None):
    val = request.session.get(cookie)
    if not val:
        val = default_val
    return val


def visitor_cookie_handler(request):
    # Get the number of visits to the site.
    # We use the COOKIES.get() function to obtain the visits cookie.
    # If the cookie exists, the value returned is casted to an integer.
    # If the cookie doesn't exist, then the default value of 1 is used.
    visits = int(get_server_side_cookie(request, 'visits', '1'))

    last_visit_cookie = get_server_side_cookie(request, 'last_visit',
                                               str(datetime.now()) )

    last_visit_time = datetime.strptime(last_visit_cookie[:-7],
                                        "%Y-%m-%d %H:%M:%S")
    #last_visit_time = datetime.now()
    # If it's been more than a day since the last visit...
    if (datetime.now() - last_visit_time).seconds > 0:
        visits = visits + 1
        #update the last visit cookie now that we have updated the count
        request.session['last_visit'] = str(datetime.now())
    else:
        visits = 1
        # set the last visit cookie
        request.session['last_visit'] = last_visit_cookie
    # update/set the visits cookie
    request.session['visits'] = visits


def index(request):
    # Get top 5 categories in order of likes.
    category_list = Category.objects.order_by('-likes')[:5]
    pages_list = Page.objects.order_by('-views')[:5]
    context_dict = {'categories': category_list, 'pages': pages_list}

    # Call the helper function to handle the cookies
    visitor_cookie_handler(request)
    context_dict['visits'] = request.session['visits']

    # Return response back to the user, updating any cookies that need chan
    return render(request, 'rango/index.html', context_dict)


def about(request):
    # Cookie test
    if request.session.test_cookie_worked():
        print("TEST COOKIE WORKED!")
        request.session.delete_test_cookie()
    # Cookie test over
    response = render(request, 'rango/about.html')
    # Call the helper function to handle the cookies
    visitor_cookie_handler(request)
    context_dict = {'visits': 0}
    context_dict['visits'] = request.session['visits']
    return response


def show_category(request, category_name_slug):
    # Create a context dictionary which we can pass
    # to the template rendering engine.
    context_dict = {}

    try:
        # .get() returns a model instance matching slug, or raises exception
        # if slug doesn't exist.
        category = Category.objects.get(slug=category_name_slug)

        # Retrieve list of page objects, or an empty list, and sort by views.
        pages = Page.objects.filter(category=category).order_by('-views')

        # Add results list to template context under name pages.
        context_dict['pages'] = pages

        # Add category object from database to context dictionary
        # to be used in template to verify that category exists.
        context_dict['category'] = category

    except Category.DoesNotExist:
        # Template will display "no category" message.
        context_dict['category'] = None
        context_dict['pages'] = None
        
    # Added for search form
    context_dict['query'] = category.name
    
    result_list = []
    if request.method == 'POST':
        query = request.POST['query'].strip()
        
        if query:
            # Run our search API function to get the results list!
            result_list = run_query(query)
            context_dict['query'] = query
            context_dict['result_list'] = result_list
    
    # Go render the response and return it to the client.
    return render(request, 'rango/category.html', context_dict)


def add_category(request):
    form = CategoryForm()

    if request.method == 'POST':
        form = CategoryForm(request.POST)

        if form.is_valid():
            form.save(commit=True)

            return index(request)
        else:
            print(form.errors)

    return render(request, 'rango/add_category.html', {'form': form})


def add_page(request, category_name_slug):
    try:
        category = Category.objects.get(slug=category_name_slug)
    except Category.DoesNotExist:
        category = None

    form = PageForm()
    if request.method == 'POST':
        form = PageForm(request.POST)
        if form.is_valid():
            if category:
                page = form.save(commit=False)
                page.category = category
                page.views = 0
                page.save()
                return show_category(request, category_name_slug)
            else:
                print(form.errors)

    context_dict = {'form': form, 'category': category}
    return render(request, 'rango/add_page.html', context_dict)


def search(request):
    result_list = []
    query = ""

    if request.method == 'POST':
        query = request.POST['query'].strip()
        if query:
            # Run Webhouse search function to get the list.
            result_list = run_query(query)

    return render(request, 'rango/search.html',
                  {'result_list': result_list, 'query': query})


def track_url(request):
    page_id = None
    url = '/rango/'
    if request.method == 'GET':
        if 'page_id' in request.GET:
            page_id = request.GET['page_id']
            
            try:
                page = Page.objects.get(id=page_id)
                page.views += 1
                page.save()
                url = page.url
            except:
                pass
            
    return redirect(url)

@login_required
def register_profile(request):
    form = UserProfileForm()

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES)
        if form.is_valid():
            user_profile = form.save(commit=False)
            user_profile.user = request.user
            user_profile.save()

            return redirect('index')
        else:
            print(form.errors)

    context_dict = {'form': form}

    return render(request, 'rango/profile_registration.html', context_dict)


@login_required
def profile(request, username):
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return redirect('index')

    userprofile = UserProfile.objects.get_or_create(user=user)[0]
    form = UserProfileForm({'website': userprofile.website,
                            'picture': userprofile.picture})

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=userprofile)
        if form.is_valid():
            form.save(commit=True)
            return redirect('profile', user.username)
        else:
            print(form.errors)

    return render(request, 'rango/profile.html', {'userprofile': userprofile,
                                                  'selecteduser': user,
                                                  'form': form})


@login_required
def list_profiles(request):
    userprofile_list = UserProfile.objects.all()

    return render(request, 'rango/list_profiles.html', {'userprofile_list': userprofile_list})
