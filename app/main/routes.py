from flask import render_template, redirect, url_for, flash, request, jsonify, Response, current_app
from flask_login import login_required, current_user
from app import db
from app.main.forms import ClientForm, SearchQueryForm, PromptForm
from app.models.client import Client
from app.models.search_query import SearchQuery
from app.tasks.search_tasks import run_search
from app.models.task import SearchTask
from app.models.prompt import Prompt
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
    
    # Create task in DB
    task = SearchTask(
        client_id=id,
        search_query_id=search_query_id,
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
        
        # Добавляем поля промпта
        for i, field_form in enumerate(form.fields):
            field = PromptField(
                prompt=prompt,
                name=field_form.name.data,
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
    
    if form.validate_on_submit():
        prompt.content = form.content.data
        prompt.description = form.description.data
        
        # Обработка активного статуса
        if form.is_active.data and not prompt.is_active:
            Prompt.query.filter_by(client_id=id, is_active=True).update({'is_active': False})
        prompt.is_active = form.is_active.data
        
        # Обновляем поля
        # Сначала удаляем старые
        PromptField.query.filter_by(prompt_id=prompt.id).delete()
        
        # Добавляем новые
        for i, field_form in enumerate(form.fields):
            field = PromptField(
                prompt=prompt,
                name=field_form.name.data,
                description=field_form.description.data,
                field_type=field_form.field_type.data,
                order=i,
                is_required=field_form.is_required.data
            )
            db.session.add(field)
        
        db.session.commit()
        flash('Prompt updated successfully', 'success')
        return redirect(url_for('main.client_prompts', id=id))
    
    # Заполняем форму текущими полями
    while len(form.fields) < len(prompt.fields):
        form.fields.append_entry()
    for i, field in enumerate(prompt.fields):
        form.fields[i].name.data = field.name
        form.fields[i].description.data = field.description
        form.fields[i].field_type.data = field.field_type
        form.fields[i].is_required.data = field.is_required
    
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
    
    # Создаем CSV
    output = StringIO()
    writer = csv.writer(output)
    
    # Заголовки зависят от типа промпта
    headers = ['URL', 'Title', 'Published Date', 'Domain']
    if task.prompt and task.prompt.content and 'B2B Lead Analysis' in task.prompt.content:
        headers.extend(['Company Name', 'Potential Score', 'Sales Notes', 
                       'Company Description', 'Annual Revenue', 'Country',
                       'Website', 'Assumed Website'])
    
    writer.writerow(headers)
    
    for result in results:
        row = [
            result.url,
            result.title,
            result.published_date.strftime('%d.%m.%Y') if result.published_date else '',
            result.domain
        ]
        
        # Если есть анализ, разбираем его
        if result.analysis:
            try:
                analysis_list = eval(result.analysis)
                if len(analysis_list) >= 8:  # B2B Lead Analysis
                    row.extend([
                        analysis_list[0],  # Company Name
                        analysis_list[1],  # Potential Score
                        analysis_list[2],  # Sales Notes
                        analysis_list[3],  # Company Description
                        analysis_list[4],  # Annual Revenue
                        analysis_list[5],  # Country
                        analysis_list[6],  # Website
                        analysis_list[7]   # Assumed Website
                    ])
            except Exception as e:
                app.logger.error(f"Error parsing analysis: {str(e)}")
                row.extend([''] * 8)  # Добавляем пустые значения при ошибке
        
        writer.writerow(row)
    
    output.seek(0)
    return Response(
        output,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment;filename=results_{task_id}.csv'}
    )

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
