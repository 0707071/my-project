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
        flash('Клиент успешно создан', 'success')
        return redirect(url_for('main.clients'))
    return render_template('main/client_form.html', form=form, title='Новый клиент')

@bp.route('/client/<int:id>')
@login_required
def client_detail(id):
    client = Client.query.get_or_404(id)
    return render_template('main/client_detail.html', client=client)

@bp.route('/client/<int:id>/search', methods=['GET', 'POST'])
@login_required
def client_search(id):
    client = Client.query.get_or_404(id)
    form = SearchQueryForm()
    
    if form.validate_on_submit():
        # Получаем последнюю версию зароса
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
        flash('Поисковый запрос сохранен', 'success')
        return redirect(url_for('main.client_detail', id=id))
        
    return render_template('main/search_form.html', form=form, client=client)

@bp.route('/client/<int:id>/search/run', methods=['POST'])
@login_required
def run_client_search(id):
    client = Client.query.get_or_404(id)
    search_query_id = request.form.get('search_query_id')
    
    if not search_query_id:
        flash('Не выбран поисковый запрос', 'danger')
        return redirect(url_for('main.client_detail', id=id))
    
    # Создаем задачу в БД
    task = SearchTask(
        client_id=id,
        search_query_id=search_query_id,
        status='pending'
    )
    db.session.add(task)
    db.session.commit()
    
    # Запускаем асинхронную задачу
    celery_task = run_search.delay(task.id)
    task.celery_task_id = celery_task.id
    db.session.commit()
    
    flash('Поиск запущен', 'success')
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
        
        prompt = Prompt(
            client_id=id,
            version=new_version,
            content=form.content.data,
            description=form.description.data,
            is_active=form.is_active.data,
            created_by_id=current_user.id
        )
        
        if form.is_active.data:
            # Деактивируем другие промпты
            Prompt.query.filter_by(client_id=id, is_active=True).update({'is_active': False})
            
        db.session.add(prompt)
        db.session.commit()
        flash('Промпт успешно создан', 'success')
        return redirect(url_for('main.client_prompts', id=id))
        
    return render_template('main/prompt_form.html', form=form, client=client, title='Новый промпт')

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
    
    # Создаем CSV файл
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['URL', 'Заголовок', 'Сниппет', 'Дата публикации', 'Домен'])
    
    for result in results:
        writer.writerow([
            result.url,
            result.title,
            result.snippet,
            result.published_date.strftime('%d.%m.%Y') if result.published_date else '',
            result.domain
        ])
    
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
    current_app.logger.info(f'Available routes: {routes}')  # Добавим логирование маршрутов
    return jsonify(routes)
