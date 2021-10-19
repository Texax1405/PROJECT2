from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class User(AbstractUser):
    pass
class Category(models.Model):
    category = models.CharField(max_length=64)

    def __str__(self):
        return f"{self.category}"

class Listingitems(models.Model):
    title = models.CharField(max_length=64)
    create_date = models.DateTimeField(default=timezone.now)
    flActive  = models.BooleanField(default=True)
    description = models.CharField(null=True, max_length=160)
    startingcost = models.FloatField()
    currentcost =  models.FloatField(blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="similar_list")
    seller = models.ForeignKey(User, on_delete=models.PROTECT, related_name="all_list")
    watching_listing = models.ManyToManyField(User, blank=True, related_name="watch_list")
    purchase = models.ForeignKey(User, null=True, on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.title} - {self.startingcost}"

class Bid(models.Model):
    auction = models.ForeignKey(Listingitems, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    offer = models.FloatField()
    date = models.DateTimeField(auto_now = True)

class comment(models.Model):
    comment = models.CharField(max_length=160)
    createtime = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    listing = models.ForeignKey(Listingitems, on_delete=models.CASCADE, related_name="get_comment")

    def take_comment_date(self):
        return self.createtime.strftime("%m/%d/%Y, %H:%M:%S")

class Picture(models.Model):
    listing = models.ForeignKey(Listingitems, on_delete=models.CASCADE, related_name="get_picture")
    picture = models.ImageField(upload_to = "images/")
    alt = models.CharField(max_length=100)