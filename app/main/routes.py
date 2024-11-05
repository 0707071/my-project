from flask import render_template, redirect, url_for, flash, request, jsonify, Response, current_app
from flask_login import login_required, current_user
from app import db
from app.main.forms import ClientForm, SearchQueryForm, PromptForm
from app.models.client import Client
from app.models.search_query import SearchQuery
from app.tasks.search_tasks import run_search
from app.models.task import SearchTask
from app.models.prompt import Prompt, PromptField
from app.models.search_result import SearchResult
from app.main import bp
import csv
from io import StringIO

@bp.route('/')
@login_required
def index():
    current_app.logger.info('Accessing index page')
    try:
        return render_template('main/index.html')
    except Exception as e:
        current_app.logger.error(f'Error rendering index page: {str(e)}')
        return str(e), 500

@bp.route('/clients')
@login_required
def clients():
    clients = Client.query.filter_by(is_active=True).all()
    return render_template('main/clients.html', clients=clients)

@bp.route('/client/new', methods=['GET', 'POST'])
@login_required
def new_client():
    form = ClientForm()
    if form.validate_on_submit():
        client = Client(
            name=form.name.data,
            description=form.description.data,
            is_active=True
        )
        db.session.add(client)
        db.session.commit()
        flash('Client created successfully', 'success')
        return redirect(url_for('main.clients'))
    return render_template('main/client_form.html', form=form, title='New Client')

@bp.route('/client/<int:id>')
@login_required
def client_detail(id):
    client = Client.query.get_or_404(id)
    return render_template('main/client_detail.html', client=client, SearchTask=SearchTask)

@bp.route('/client/<int:id>/search', methods=['GET', 'POST'])
@login_required
def client_search(id):
    client = Client.query.get_or_404(id)
    form = SearchQueryForm()
    
    if form.validate_on_submit():
        # Get the latest query version
        last_query = SearchQuery.query.filter_by(client_id=id).order_by(SearchQuery.version.desc()).first()
        new_version = 1 if not last_query else last_query.version + 1
        
        query = SearchQuery(
            client_id=id,
            version=new_version,
            main_phrases=form.main_phrases.data,
            include_words=form.include_words.data,
            exclude_words=form.exclude_words.data,
            notes=form.notes.data,
            is_active=form.is_active.data
        )
        db.session.add(query)
        db.session.commit()
        flash('Search query saved', 'success')
        return redirect(url_for('main.client_detail', id=id))
        
    return render_template('main/search_form.html', form=form, client=client)

@bp.route('/client/<int:id>/search/run', methods=['POST'])
@login_required
def run_client_search(id):
    client = Client.query.get_or_404(id)
    search_query_id = request.form.get('search_query_id')
    
    if not search_query_id:
        flash('No search query selected', 'danger')
        return redirect(url_for('main.client_detail', id=id))
    
    # Получаем активный промпт клиента
    active_prompt = Prompt.query.filter_by(client_id=id, is_active=True).first()
    if not active_prompt:
        flash('No active prompt found', 'danger')
        return redirect(url_for('main.client_detail', id=id))
    
    # Create task in DB
    task = SearchTask(
        client_id=id,
        search_query_id=search_query_id,
        prompt_id=active_prompt.id,  # Добавляем prompt_id
        status='pending'
    )
    db.session.add(task)
    db.session.commit()
    
    # Start async task
    celery_task = run_search.delay(task.id)
    task.celery_task_id = celery_task.id
    db.session.commit()
    
    flash('Search started', 'success')
    return redirect(url_for('main.task_status', task_id=task.id))

@bp.route('/task/<int:task_id>')
@login_required
def task_status(task_id):
    task = SearchTask.query.get_or_404(task_id)
    return render_template('main/task_status.html', task=task)

@bp.route('/task/<int:task_id>/status')
@login_required
def get_task_status(task_id):
    task = SearchTask.query.get_or_404(task_id)
    return jsonify({
        'status': task.status,
        'progress': task.progress,
        'error': task.error_message
    })

@bp.route('/client/<int:id>/prompts')
@login_required
def client_prompts(id):
    client = Client.query.get_or_404(id)
    prompts = Prompt.query.filter_by(client_id=id).order_by(Prompt.version.desc()).all()
    return render_template('main/prompts.html', client=client, prompts=prompts)

@bp.route('/client/<int:id>/prompt/new', methods=['GET', 'POST'])
@login_required
def new_prompt(id):
    client = Client.query.get_or_404(id)
    form = PromptForm()
    
    if form.validate_on_submit():
        # Получаем последнюю версию промпта
        last_prompt = Prompt.query.filter_by(client_id=id).order_by(Prompt.version.desc()).first()
        new_version = 1 if not last_prompt else last_prompt.version + 1
        
        # Создаем новый промпт
        prompt = Prompt(
            client_id=id,
            version=new_version,
            content=form.content.data,
            description=form.description.data,
            is_active=form.is_active.data,
            created_by_id=current_user.id
        )
        
        # Если промпт активный, деактивируем остальные
        if form.is_active.data:
            Prompt.query.filter_by(client_id=id, is_active=True).update({'is_active': False})
        
        db.session.add(prompt)
        db.session.flush()  # Получаем id нового промпта
        
        # Добавляем поля промпта из текстового поля
        column_names = [name.strip() for name in form.column_names.data.split('\n') if name.strip()]
        for i, name in enumerate(column_names):
            field = PromptField(
                prompt_id=prompt.id,  # Используем prompt_id вместо prompt
                name=name,
                order=i
            )
            db.session.add(field)
        
        try:
            db.session.commit()
            flash('Prompt created successfully', 'success')
            return redirect(url_for('main.client_detail', id=id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating prompt: {str(e)}', 'danger')
    
    return render_template('main/prompt_form.html', form=form, client=client, title='New Prompt')

@bp.route('/client/<int:id>/prompt/<int:prompt_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_prompt(id, prompt_id):
    client = Client.query.get_or_404(id)
    prompt = Prompt.query.get_or_404(prompt_id)
    
    if prompt.client_id != id:
        flash('Access denied', 'danger')
        return redirect(url_for('main.client_prompts', id=id))
    
    form = PromptForm(obj=prompt)
    
    if request.method == 'POST':
        current_app.logger.info(f'POST request received')
        current_app.logger.info(f'Form data: {request.form}')
    
    if form.validate_on_submit():
        current_app.logger.info('Form validated successfully')
        try:
            # Сохраняем старые значения для логирования
            old_content = prompt.content
            old_description = prompt.description
            
            # Обновляем данные промпта
            prompt.content = form.content.data
            prompt.description = form.description.data
            prompt.is_active = form.is_active.data
            
            current_app.logger.info(f'Content changed from: {old_content[:100]} to: {prompt.content[:100]}')
            
            # Обработка активного статуса
            if form.is_active.data and not prompt.is_active:
                Prompt.query.filter_by(client_id=id, is_active=True).update({'is_active': False})
            
            # Обновляем поля
            PromptField.query.filter_by(prompt_id=prompt.id).delete()
            column_names = [name.strip() for name in form.column_names.data.split('\n') if name.strip()]
            current_app.logger.info(f'New column names: {column_names}')
            
            for i, name in enumerate(column_names):
                field = PromptField(
                    prompt_id=prompt.id,
                    name=name,
                    order=i
                )
                db.session.add(field)
            
            db.session.commit()
            flash('Prompt updated successfully', 'success')
            current_app.logger.info('Changes committed successfully')
            return redirect(url_for('main.client_detail', id=id))
            
        except Exception as e:
            current_app.logger.error(f'Error updating prompt: {str(e)}')
            db.session.rollback()
            flash(f'Error updating prompt: {str(e)}', 'danger')
    else:
        if form.errors:
            current_app.logger.error(f'Form validation errors: {form.errors}')
        if request.method == 'POST':
            flash('Please check the form for errors', 'danger')
    
    # При GET запросе заполняем поле column_names существующими полями
    if not form.column_names.data:
        fields = PromptField.query.filter_by(prompt_id=prompt.id).order_by(PromptField.order).all()
        form.column_names.data = '\n'.join(field.name for field in fields)
        current_app.logger.info(f'Loaded existing column names: {form.column_names.data}')
    
    return render_template('main/prompt_form.html', form=form, client=client, prompt=prompt, title='Edit Prompt')

@bp.route('/client/<int:id>/prompt/<int:prompt_id>/activate', methods=['POST'])
@login_required
def activate_prompt(id, prompt_id):
    client = Client.query.get_or_404(id)
    prompt = Prompt.query.get_or_404(prompt_id)
    
    if prompt.client_id != id:
        flash('Access denied', 'danger')
        return redirect(url_for('main.client_prompts', id=id))
    
    # Деактивируем текущий активный промпт
    Prompt.query.filter_by(client_id=id, is_active=True).update({'is_active': False})
    
    # Активируем выбранный промпт
    prompt.is_active = True
    db.session.commit()
    
    flash('Prompt activated successfully', 'success')
    return redirect(url_for('main.client_prompts', id=id))

@bp.route('/client/<int:id>/prompt/<int:prompt_id>/delete', methods=['POST'])
@login_required
def delete_prompt(id, prompt_id):
    client = Client.query.get_or_404(id)
    prompt = Prompt.query.get_or_404(prompt_id)
    
    if prompt.client_id != id:
        flash('Access denied', 'danger')
        return redirect(url_for('main.client_prompts', id=id))
    
    # Не даем удалить активный промпт
    if prompt.is_active:
        flash('Cannot delete active prompt', 'danger')
        return redirect(url_for('main.client_prompts', id=id))
    
    # Удаляем промпт и его поля
    db.session.delete(prompt)
    db.session.commit()
    
    flash('Prompt deleted successfully', 'success')
    return redirect(url_for('main.client_prompts', id=id))

@bp.route('/prompt/<int:id>')
@login_required
def prompt_detail(id):
    prompt = Prompt.query.get_or_404(id)
    return render_template('main/prompt_detail.html', prompt=prompt)

@bp.route('/task/<int:task_id>/results')
@login_required
def task_results(task_id):
    task = SearchTask.query.get_or_404(task_id)
    page = request.args.get('page', 1, type=int)
    results = SearchResult.query.filter_by(task_id=task_id).paginate(
        page=page, per_page=20, error_out=False)
    return render_template('main/results.html', task=task, results=results)

@bp.route('/task/<int:task_id>/export')
@login_required
def export_results(task_id):
    task = SearchTask.query.get_or_404(task_id)
    results = SearchResult.query.filter_by(task_id=task_id).all()
    
    try:
        # Создаем CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Получаем поля промпта в правильном порядке
        prompt_fields = []
        if task.prompt:
            prompt_fields = PromptField.query.filter_by(
                prompt_id=task.prompt_id
            ).order_by(PromptField.order).all()
        
        # Формируем заголовки
        headers = ['URL', 'Title', 'Published Date', 'Domain']
        if prompt_fields:
            headers.extend([field.name for field in prompt_fields])
        
        writer.writerow(headers)
        
        for result in results:
            try:
                # Базовые поля
                row = [
                    result.url,
                    result.title,
                    result.published_date.strftime('%d.%m.%Y') if result.published_date else '',
                    result.domain
                ]
                
                # Добавляем разобранные поля анализа
                if prompt_fields:
                    parsed_analysis = result.parse_analysis()
                    row.extend([parsed_analysis.get(field.name, '') for field in prompt_fields])
                
                writer.writerow(row)
            except Exception as e:
                current_app.logger.error(f"Error processing result {result.id}: {str(e)}")
                continue
        
        output.seek(0)
        return Response(
            output,
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment;filename=results_{task_id}.csv'}
        )
    except Exception as e:
        current_app.logger.error(f"Error exporting results: {str(e)}")
        flash('Error exporting results', 'danger')
        return redirect(url_for('main.task_results', task_id=task_id))

@bp.route('/debug')
def debug():
    current_app.logger.info('Accessing debug page')
    routes = []
    for rule in current_app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'methods': list(rule.methods),
            'url': str(rule)
        })
    current_app.logger.info(f'Available routes: {routes}')  # Add routes logging
    return jsonify(routes)

<<<<<<< HEAD
@bp.route('/client/<int:id>/search/<int:query_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_search_query(id, query_id):
    client = Client.query.get_or_404(id)
    query = SearchQuery.query.get_or_404(query_id)
    
    # Проверяем, принадлежит ли запрос этому клиенту
    if query.client_id != id:
        flash('Access denied', 'danger')
        return redirect(url_for('main.client_detail', id=id))
    
    form = SearchQueryForm(obj=query)
    
    if form.validate_on_submit():
        query.main_phrases = form.main_phrases.data
        query.include_words = form.include_words.data
        query.exclude_words = form.exclude_words.data
        query.notes = form.notes.data
        query.is_active = form.is_active.data
        query.days_back = form.days_back.data
        query.results_per_page = form.results_per_page.data
        query.num_pages = form.num_pages.data
        
        db.session.commit()
        flash('Search query updated', 'success')
        return redirect(url_for('main.client_detail', id=id))
        
    return render_template('main/search_form.html', form=form, client=client, title='Edit Search Query')

@bp.route('/client/<int:id>/search/<int:query_id>/delete', methods=['POST'])
@login_required
def delete_search_query(id, query_id):
    client = Client.query.get_or_404(id)
    query = SearchQuery.query.get_or_404(query_id)
    
    # Проверяем, принадлежит ли запрос этому клиенту
    if query.client_id != id:
        flash('Access denied', 'danger')
        return redirect(url_for('main.client_detail', id=id))
    
    # Удаляем связанные задачи и результаты
    for task in query.tasks:
        SearchResult.query.filter_by(task_id=task.id).delete()
        db.session.delete(task)
    
    db.session.delete(query)
    db.session.commit()
    
    flash('Search query deleted', 'success')
    return redirect(url_for('main.client_detail', id=id))
=======
@bp.route('/parser')
@login_required
def parser():
    return render_template('main/parser.html')  # Ensure this points to the correct template
>>>>>>> 7897752 (The local changes)
