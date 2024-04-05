# blog/views.py

from django.shortcuts import render, redirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import LoginForm, SignupForm, BlogForm
from .models import BlogModel
from django.views.generic import ListView, DetailView,DeleteView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.shortcuts import render
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required


def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')  # redirect to home page after login
            else:
                error_message = "Invalid username or password"
    else:
        form = LoginForm()
        error_message = "Invalid request"
    return render(request, 'blog/login.html', {'form': form, 'error_message': error_message})

def user_signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            return redirect('dashboard')  # Redirect to dashboard after successful signup
    else:
        form = SignupForm()
    return render(request, 'blog/signup.html', {'form': form})


@login_required
def user_logout(request):
    logout(request)
    return redirect('login')


def dashboard(request):
    # Get all blog posts
    all_posts = BlogModel.objects.all()

    # Paginate the blog posts
    paginator = Paginator(all_posts, 5)  # Show 5 blog posts per page
    page = request.GET.get('page')

    try:
        blog_posts = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        blog_posts = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results
        blog_posts = paginator.page(paginator.num_pages)

    return render(request, 'blog/dashboard.html', {'blog_posts': blog_posts})

@login_required
def add_blog(request):
    if request.method == 'POST':
        form = BlogForm(request.POST, request.FILES)
        if form.is_valid():
            title = form.cleaned_data['title']
            content = form.cleaned_data['content']
            user = request.user
            image = form.cleaned_data['image']
            tags = form.cleaned_data['tags']
            print("Tags:", tags)  # Debug print
            
            blog_obj = BlogModel.objects.create(
                user=user, title=title,
                content=content, image=image
            )
            blog_obj.tags.set(tags)
            
            return redirect('dashboard')  # Redirect to the dashboard after successful creation
    else:
        form = BlogForm()
    return render(request, 'blog/add_blog.html', {'form': form})

class BlogListView(LoginRequiredMixin, ListView):
    model = BlogModel
    template_name = 'blog/blog_list.html'
    context_object_name = 'blog_posts'

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset().filter(user=user)
        return queryset

class BlogDetailView(DetailView):
    model = BlogModel
    template_name = 'blog/blog_detail.html'
    context_object_name = 'post'

class BlogDeleteView(DeleteView):
    model = BlogModel
    template_name = 'blog/blog_confirm_delete.html'
    success_url = reverse_lazy('blog_list') 


@login_required
def update_blog(request, pk):
    blog = get_object_or_404(BlogModel, pk=pk)
    if request.method == 'POST':
        form = BlogForm(request.POST, request.FILES, instance=blog)
        if form.is_valid():
            form.save()
            return redirect('blog_detail', slug=blog.slug)
    else:
        form = BlogForm(instance=blog)
    return render(request, 'blog/update_blog.html', {'form': form, 'blog': blog})


def search_blog(request):
    query = request.GET.get('query')  # Get the query
    tag_query = None
    results = []

    if query:
        # Perform search on title and content using Q objects
        content_results = BlogModel.objects.filter(
            Q(title__icontains=query) | Q(content__icontains=query)
        ).distinct()
        
        # Extend results with content-based search results
        results.extend(content_results)

    tag_query = request.GET.get('query')  # Get the tag query
    
    if tag_query:
        # Perform tag-based search
        tag_results = BlogModel.objects.filter(tags__name=tag_query)
        
        # Extend results with tag-based search results
        results.extend(tag_results)

    # Sort and deduplicate the results
    results = sorted(set(results), key=lambda x: x.pk, reverse=True)[:10]

    return render(request, 'blog/search_results.html', {'blog_posts': results, 'query': query, 'tag_query': tag_query})


def send_email(request):
    if request.method == 'POST':
        blog_id = request.POST.get('blog_id')
        recipient_name = request.POST.get('recipient_name')
        recipient_email = request.POST.get('recipient_email')
        comments = request.POST.get('comments')
        
        # Retrieve the blog object
        blog = BlogModel.objects.get(pk=blog_id)
        
        # Send the email with blog title, content, image, tags, published at, published by, and comments
        send_email_with_comments(
            blog.title,
            blog.content,
            comments,
            recipient_email,
            blog.image,  # Assuming `image` is the field name for the blog image
            blog.tags.all(),  # Assuming `tags` is the ManyToManyField for tags
            blog.created_at,  # Assuming `created_at` is the field for published at
            blog.user.username  # Assuming `user` is the ForeignKey to the author/user model
        )
        
        # Redirect back to the blog detail page after sending email
        return redirect('dashboard')

def send_email_with_comments(blog_title, blog_content, comments, recipient_email, blog_image, blog_tags, published_at, published_by):
    # Render the email content using a template
    email_subject = f"Check out this blog: {blog_title}"
    email_template = 'email_templates/share_blog_email.html'
    email_context = {
        'blog_title': blog_title,
        'blog_content': blog_content,
        'comments': comments,
        'blog_image': blog_image,
        'blog_tags': blog_tags,
        'published_at': published_at,
        'published_by': published_by,
    }
    email_body = render_to_string(email_template, email_context)

    # Create an EmailMessage instance
    email = EmailMessage(
        subject=email_subject,
        body=email_body,
        from_email='singhtanvir0029@gmail.com',  # Sender's email address
        to=[recipient_email],  # Recipient(s)
    )
    email.content_subtype = 'html'  # Set content type to HTML

    # Attach the image file
    email.attach_file(blog_image.path)  # Assuming blog_image is an ImageField

    # Send the email
    email.send()

def share_blog_email(request, blog_id):
    blog = BlogModel.objects.get(id=blog_id)
    return render(request, 'email_templates/email_form.html', {'blog': blog})