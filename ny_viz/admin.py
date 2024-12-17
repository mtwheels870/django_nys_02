from django.contrib import admin

from .models import Question, Choice

class ChoiceInline(admin.StackedInline):
    model = Choice
    extra = 3

class QuestionAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {"fields": ["question_text"]}),
        ("Date Information", {"fields": ["pub_date"], 
            "classes": ["collapse"]}),
    ]
    inlines = [ChoiceInLine]

# Register your models here.
admin.site.register(Question, QuestionAdmin)
