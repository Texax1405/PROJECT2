from django.contrib import admin
from .models import Category, Listingitems, Bid, comment, Picture

# Register your models here.

admin.site.register(Category)
admin.site.register(Listingitems)
admin.site.register(Bid)
admin.site.register(comment)
admin.site.register(Picture)