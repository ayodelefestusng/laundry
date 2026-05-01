from django.db import models
from .models import TenantModel

class LandingCarousel(TenantModel):
    image = models.ImageField(upload_to="landing/carousel/", help_text="Carousel background image")
    title = models.CharField(max_length=255, help_text="Main heading")
    subtitle = models.TextField(blank=True, null=True)
    transition_speed = models.PositiveIntegerField(default=5000, help_text="Speed in ms (e.g. 5000 for 5s)")
    
    def __str__(self):
        return f"Carousel: {self.title}"

class LandingText(TenantModel):
    hero_title = models.CharField(max_length=255, default="Laundry Made Simple, Fresh & Fast")
    hero_subtitle = models.TextField(default="Experience premium laundry care with the touch of a button. We handle the dirty work so you can focus on what matters.")
    
    def __str__(self):
        return "Landing Hero Text"

class LandingValue(TenantModel):
    value_text = models.CharField(max_length=100, help_text="e.g. Free Pickup")
    value_subtext = models.CharField(max_length=200, help_text="e.g. From your doorstep")
    icon_class = models.CharField(max_length=50, default="fas fa-truck", help_text="FontAwesome class e.g. fas fa-truck")
    
    def __str__(self):
        return self.value_text

class LandingCommitment(TenantModel):
    image = models.ImageField(upload_to="landing/commitment/", null=True, blank=True)
    committed_to = models.CharField(max_length=200, default="Committed to Garment Care and Our Community")
    we_believe = models.TextField(help_text="We believe... text")
    eco_friendly = models.TextField(help_text="Non-toxic Detergents: Safe for sensitive skin and the environment.")
    
    def __str__(self):
        return "Landing Commitment"

class LandingPricingCard(TenantModel):
    title = models.CharField(max_length=100, help_text="e.g. Wash & Fold")
    is_popular = models.BooleanField(default=False)
    description = models.CharField(max_length=255, help_text="e.g. Perfect for everyday wear")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    features = models.JSONField(default=list, help_text="List of features")
    
    def __str__(self):
        return f"Pricing: {self.title}"

class LandingCustomerStory(TenantModel):
    story = models.TextField()
    name = models.CharField(max_length=100)
    stars = models.PositiveSmallIntegerField(default=5)
    is_verified = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Story by {self.name}"

class LandingFAQ(TenantModel):
    question = models.CharField(max_length=255)
    answer = models.TextField()
    
    def __str__(self):
        return self.question
