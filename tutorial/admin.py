from django.contrib import admin

from .models import Question, Choice

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 3

class QuestionAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {"fields": ["question_text"]}),
        ("Date Information", {"fields": ["pub_date"], 
            "classes": ["collapse"]}),
    ]
    inlines = [ChoiceInline]

# Register your models here.
# Take this out, so it won't show up in production
# admin.site.register(Question, QuestionAdmin)
