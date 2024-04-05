from django.contrib.auth.models import AbstractUser
from django.db import models
from froala_editor.fields import FroalaField
from django.utils.text import slugify
from taggit.managers import TaggableManager
from django.contrib.postgres.search import SearchVectorField


class CustomUser(AbstractUser):
    # Add custom fields here
    age = models.IntegerField(null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    # Add other fields as needed

    def __str__(self):
        return self.username
    
class BlogModel(models.Model):
    title = models.CharField(max_length=1000)
    content = FroalaField()
    slug = models.SlugField(max_length=1000, null=True, blank=True)
    user = models.ForeignKey(CustomUser, blank=True, null=True, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='blog_images')
    tags = TaggableManager()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    search_vector = SearchVectorField(null=True, blank=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_slug(self.title)
        super().save(*args, **kwargs)

def generate_slug(title):
    """
    Generate a unique slug from the given title.
    """
    slug = slugify(title)
    return slug
