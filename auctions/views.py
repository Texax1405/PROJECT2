from typing import List
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.forms import ModelForm, fields, widgets, modelformset_factory
from .models import Bid, Category, Listingitems, Picture, User, comment
from django import forms
from django.contrib.auth.decorators import login_required

class newListingForm(ModelForm):
    class Meta:
        model = Listingitems
        fields = ["title", "description", "startingcost","currentcost", "category"]

class newPictureForm(ModelForm):
    class Meta:
        model = Picture
        fields = ["picture", "alt"]

class newBidForm(ModelForm):
    class Meta:
        model = Bid
        fields = ["offer"]

class newCommentForm(ModelForm):
    class Meta:
        model = comment
        fields = ["comment"]
        widgets = {
            "comment": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Leave Here"
            })
        }

def index(request):
    return render(request, "auctions/index.html")


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")

@login_required 
def newListing(request):
    #upload file 
    PictureFormSet = modelformset_factory(Picture, form=newPictureForm, extra = 4)
    if request.method == "POST":
        form = newListingForm(request.POST, request.FILES)
        #set picture 
        imagesForm = PictureFormSet(request.POST, request.FILES, queryset= Picture.objects.none())
        #consider value 
        if form.is_valid() and imagesForm.is_valid():
            # this line call django "dont send value to database yet"
            newListing = form.save(commit=False)
            newListing.seller = request.user
            newListing.save()
            for form in imagesForm.cleaned_data:
                #clean date to get new value
                if form :
                    picture = form['picture']
                    text = form['alt']
                    newPicture = Picture(listing = newListing, picture=picture, alt = text)
                    newPicture.save()

            return render(request, "aucions/newListing.html",{
                "form": newListingForm(),
                "imageForm": PictureFormSet(queryset= Picture.objects.none()),
                "success": True
            })
        else:
            return render(request, "auctions/newListing.html",{
                "form": newListingForm(),
                "imageForm": PictureFormSet(queryset=Picture.objects.none())
            })  
    else:
        return render(request, "auctions/newListing.html",{
                "form": newListingForm(),
                "imageForm": PictureFormSet(queryset=Picture.objects.none())
            }) 

@login_required
def watchlist(request):
    listings = request.user.watch_list.all()
    categories = Category.objects.all()
    for listing in listings:
        listing.mainPicture = listing.get_picture.first()
        if request.user in listing.watching_listing.all():
            listing.is_watched = True
        else:
            listing.is_watched = False
    return render(request, "auctions/watchlist.html",{
        "listing": listings,
        "page_title": "My watchlist",
        "categories": categories
    })

@login_required
def change_watchlist(request,listing_id, reverse_method):
    listing_object = Listingitems.objects.get(id=listing_id)
    if request.user in listing_object.watching_list.all():
        listing_object.watch_list.remove(request.user)
    else:
        listing_object.watch_list.add(request.user)

    if reverse_method == "listing":
        return listing(request, listing_id)
    else:
        return HttpResponseRedirect(reverse(reverse_method))

def listing(request, listing_id):
    # check value
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login")) 
    listing = Listingitems.objects.all(id=listing_id)
    if request.user in listing.watch_list.all():
        listing.is_watched = True
    else:
        listing.is_watched = False
    return render(request, "auctions/listing.html",{
        "listing": listing,
        "listing_picture": listing.get_picture.all(),
        "form": newBidForm(),
        "comment": listing.get_comment.all(),
        "comment_form": newCommentForm(),
    })

# take a bid
@login_required
def take_bid(request,listing_id):
    # get id of item in listing
    listing = Listingitems.objects.get(id=listing_id)
    offer = float(request.POST["offer"])
    if is_valid(offer,listing):
        listing.currentcost = offer
        form = newBidForm(request.POST)
        newBid = form.save(commit=False)
        newBid.auction = listing
        newBid.user = request.user
        newBid.save()
        listing.save()
        return HttpResponseRedirect(reverse("listing", args=[listing_id]))
    else:
        return render(request, "auctions/listing.html",{
            "listing": listing,
            "listing_pictures": listing.get_picture.all(),
            "form": newBidForm(),
            "error_min_value": True
        })
#check cost import from user
def is_valid(offer,listing):
    if offer >= listing.startingcost and (listing.currentcost is None or offer > listing.currentcost):
        return True
    return False

def close_listing(request, listing_id):
    listing = Listingitems.objects.get(id=listing_id)
    if request.user == listing.seller:
        listing.flActive = False
        listing.purchase = Bid.objects.filter(auction = listing).last().user
        listing.save()
        return HttpResponseRedirect(reverse("listing", args=[listing_id]))
    else:
        listing.watching_listing.add(request.user)
    return HttpResponseRedirect(reverse("watchlist"))

def activeListing(request):
    category_id = request.GET.get("category",None)
    if category_id is None:
        listings  = Listingitems.objects.filter(flActive = True)
    else:
        listings = Listingitems.objects.filter(flActive=True, category=category_id)
    categories = Category.objects.all()
    for listing in listings:
        listing.mainPicture =  listing.get_picture.first()
        if request.user in listing.watch_listing.all():
            listing.is_watched = True
        else:
            listing.is_watched = False
    
    return render(request, "auctions/index.html",{
        "listing": listings,
        "categories": categories,
        "page_title": "Active Listings"
    })

@login_required
def comment(request, listing_id):
    listing = Listingitems.objects.get(id=listing_id)
    form = newCommentForm(request.POST)
    newComment = form.save(commit=True)
    newComment.user = request.user
    newComment.listing = listing
    newComment.save()
    return HttpResponseRedirect(reverse("listing", args=[listing_id]))