import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Sum, Count, Q
from .models import Book, Habit, HabitLog, Profile
from .forms import RegisterForm, BookForm, HabitForm

# --- Authentication ---
def register_view(request):
    if request.user.is_authenticated:
        return redirect('library')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            Profile.objects.create(user=user)
            login(request, user)
            return redirect('library')
    else:
        form = RegisterForm()
    return render(request, 'tracker/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('library')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('library')
    else:
        form = AuthenticationForm()
    return render(request, 'tracker/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

# --- Pages ---
@login_required
def library_view(request):
    query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')

    books = Book.objects.filter(user=request.user)

    if query:
        books = books.filter(Q(title__icontains=query) | Q(author__icontains=query))
    if status_filter:
        books = books.filter(status=status_filter)

    form = BookForm()
    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            book = form.save(commit=False)
            book.user = request.user
            book.save()
            return redirect('library')

    return render(request, 'tracker/library.html', {
        'books': books,
        'form': form,
        'query': query,
        'status_filter': status_filter
    })

@login_required
def edit_book_view(request, pk):
    book = get_object_or_404(Book, pk=pk, user=request.user)
    if request.method == 'POST':
        form = BookForm(request.POST, instance=book)
        if form.is_valid():
            form.save()
            return redirect('library')
    else:
        form = BookForm(instance=book)
    return render(request, 'tracker/edit_book.html', {'form': form, 'book': book})

@login_required
def delete_book_view(request, pk):
    book = get_object_or_404(Book, pk=pk, user=request.user)
    if request.method == 'POST':
        book.delete()
        return redirect('library')
    return render(request, 'tracker/delete_confirm.html', {'object': book, 'type': 'book'})

@login_required
def habits_view(request):
    today = timezone.now().date()
    habits = Habit.objects.filter(user=request.user)
    
    logs = HabitLog.objects.filter(user=request.user, completed_on=today)
    completed_habit_ids = set(logs.filter(completed=True).values_list('habit_id', flat=True))

    form = HabitForm()
    if request.method == 'POST':
        form = HabitForm(request.POST)
        if form.is_valid():
            habit = form.save(commit=False)
            habit.user = request.user
            habit.save()
            return redirect('habits')

    habit_list = []
    for habit in habits:
        habit_list.append({
            'habit': habit,
            'is_completed': habit.id in completed_habit_ids
        })

    return render(request, 'tracker/habits.html', {
        'habit_list': habit_list,
        'form': form,
        'today': today
    })

@login_required
def edit_habit_view(request, pk):
    habit = get_object_or_404(Habit, pk=pk, user=request.user)
    if request.method == 'POST':
        form = HabitForm(request.POST, instance=habit)
        if form.is_valid():
            form.save()
            return redirect('habits')
    else:
        form = HabitForm(instance=habit)
    return render(request, 'tracker/edit_habit.html', {'form': form, 'habit': habit})

@login_required
def delete_habit_view(request, pk):
    habit = get_object_or_404(Habit, pk=pk, user=request.user)
    if request.method == 'POST':
        habit.delete()
        return redirect('habits')
    return render(request, 'tracker/delete_habit_confirm.html', {'habit': habit})

@login_required
def reset_habit_view(request, pk):
    habit = get_object_or_404(Habit, pk=pk, user=request.user)
    habit.logs.all().delete()
    habit.start_date = timezone.now().date()
    habit.save()
    return redirect('habits')

@login_required
def toggle_habit_pause(request, pk):
    habit = get_object_or_404(Habit, pk=pk, user=request.user)
    habit.active = not habit.active
    habit.paused_at = timezone.now().date() if not habit.active else None
    habit.save()
    return redirect('habits')

# --- AJAX View ---
@login_required
def toggle_habit_ajax(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            habit_id = data.get('habit_id')
            today = timezone.now().date()

            habit = get_object_or_404(Habit, id=habit_id, user=request.user)
            log, created = HabitLog.objects.get_or_create(
                user=request.user,
                habit=habit,
                completed_on=today
            )
            log.completed = not log.completed
            log.save()

            total_habits = Habit.objects.filter(user=request.user, active=True).count()
            completed_count = HabitLog.objects.filter(
                user=request.user, 
                completed_on=today, 
                completed=True
            ).count()

            progress = round((completed_count / total_habits) * 100) if total_habits > 0 else 0

            return JsonResponse({
                'status': 'success',
                'completed': log.completed,
                'progress': progress,
                'message': 'تم تحديث حالة العادة بنجاح!'
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'invalid_request'}, status=400)

@login_required
def analytics_view(request):
    books = Book.objects.filter(user=request.user)
    completed_books = books.filter(status='completed').count()
    reading_books = books.filter(status='currently_reading').count()
    total_pages = books.aggregate(Sum('pages_read'))['pages_read__sum'] or 0

    today = timezone.now().date()
    dates = [str(today - timezone.timedelta(days=i)) for i in range(6, -1, -1)]

    # تجهيز الإحصائيات لكل عادة بشكل منفصل بألوانها المخصصة
    habits = Habit.objects.filter(user=request.user)
    datasets = []
    for h in habits:
        h_logs = HabitLog.objects.filter(
            habit=h,
            completed=True,
            completed_on__gte=today - timezone.timedelta(days=7)
        )
        counts_dict = {str(item.completed_on): 1 for item in h_logs}
        data = [counts_dict.get(d, 0) for d in dates]
        datasets.append({
            'label': h.name,
            'data': data,
            'backgroundColor': h.color,
        })

    context = {
        'completed_books': completed_books,
        'reading_books': reading_books,
        'total_pages': total_pages,
        'chart_dates': json.dumps(dates),
        'chart_datasets': json.dumps(datasets),
    }
    return render(request, 'tracker/analytics.html', context)

def about_view(request):
    return render(request, 'tracker/about.html')