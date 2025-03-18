from app.main import bp
from flask import render_template, redirect, url_for, flash, request, jsonify, Response, current_app, send_file
from flask_login import login_required, current_user
from app import db
from app.main.forms import ClientForm, SearchQueryForm, PromptForm
from app.models.client import Client
from app.models.search_query import SearchQuery
from app.tasks.search_tasks import run_search
from app.models.task import SearchTask
from app.models.prompt import Prompt
from app.models.search_result import SearchResult
from app.models.export import Export
from app.models.analysis_result import AnalysisResult
import csv
from io import StringIO
import pandas as pd
from datetime import datetime
import os
import io
import openpyxl

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
            is_active=form.is_active.data,
            days_back=form.days_back.data,
            results_per_page=form.results_per_page.data,
            num_pages=form.num_pages.data
        )
        db.session.add(query)
        db.session.commit()
        flash('Search query saved', 'success')
        return redirect(url_for('main.client_detail', id=id))
        
    return render_template('main/search_form.html', form=form, client=client)

@bp.route('/client/<int:id>/search/run', methods=['POST'])
@login_required
def run_client_search(id):
    search_query_id = request.form.get('search_query_id')
    if not search_query_id:
        flash('No search query selected', 'danger')
        return redirect(url_for('main.client_detail', id=id))
    
    search_query = SearchQuery.query.get_or_404(search_query_id)
    
    # Получаем активный промпт
    prompt = Prompt.query.filter_by(
        client_id=id,
        is_active=True
    ).first()
    
    if not prompt:
        flash('No active prompt found', 'danger')
        return redirect(url_for('main.client_detail', id=id))
    
    if not prompt.column_names:
        flash('Prompt column names not configured', 'danger')
        return redirect(url_for('main.client_detail', id=id))
    
    # Создаем задачу
    task = SearchTask(
        client_id=id,
        search_query_id=search_query_id,
        prompt_id=prompt.id,
        status='pending'
    )
    db.session.add(task)
    db.session.commit()
    
    # Запускаем задачу
    try:
        celery_task = run_search.delay(task.id)
        task.celery_task_id = celery_task.id
        db.session.commit()
        print(f"DEBUG: Celery task started: {celery_task.id}")  # Добавляем отладку
    except Exception as e:
        print(f"ERROR starting Celery task: {str(e)}")  # Добавляем отладку ошибок
        flash('Error starting search task', 'danger')
        return redirect(url_for('main.client_detail', id=id))
    
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
        prompt = Prompt(
            client_id=id,
            content=form.content.data,
            description=form.description.data,
            is_active=form.is_active.data,
            column_names=form.column_names.data
        )
        
        if prompt.is_active:
            # Деактивируем другие промпты
            Prompt.query.filter_by(client_id=id, is_active=True).update({'is_active': False})
        
        db.session.add(prompt)
        db.session.commit()
        
        flash('Prompt created successfully', 'success')
        return redirect(url_for('main.client_detail', id=id))
        
    return render_template('main/prompt_form.html', form=form, client=client)

@bp.route('/client/<int:id>/prompt/<int:prompt_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_prompt(id, prompt_id):
    client = Client.query.get_or_404(id)
    prompt = Prompt.query.get_or_404(prompt_id)
    
    if prompt.client_id != id:
        flash('Access denied', 'danger')
        return redirect(url_for('main.client_detail', id=id))
    
    form = PromptForm(obj=prompt)
    
    if form.validate_on_submit():
        prompt.content = form.content.data
        prompt.description = form.description.data
        prompt.column_names = form.column_names.data
        
        if form.is_active.data and not prompt.is_active:
            # Деактивируем другие промпты
            Prompt.query.filter_by(client_id=id, is_active=True).update({'is_active': False})
            prompt.is_active = True
        elif not form.is_active.data and prompt.is_active:
            prompt.is_active = False
        
        db.session.commit()
        flash('Prompt updated successfully', 'success')
        return redirect(url_for('main.client_detail', id=id))
        
    return render_template('main/prompt_form.html', form=form, client=client, prompt=prompt)

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

@bp.route('/task/<int:task_id>/results', methods=['GET'])
@login_required
def task_results(task_id):
    task = SearchTask.query.get_or_404(task_id)
    results = AnalysisResult.query.filter_by(task_id=task_id).all()
    
    # Если запрошено скачивание
    if request.args.get('download'):
        if task.result_file and os.path.exists(os.path.join(current_app.root_path, '..', task.result_file)):
            return send_file(
                os.path.join(current_app.root_path, '..', task.result_file),
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=f'search_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
            )
        else:
            flash('Result file not found', 'error')
    
    # Для отображения страницы
    return render_template('task/results.html', 
                         task=task,
                         results=results,
                         min_potential=request.args.get('min_potential', 0, type=int))

@bp.route('/task/<int:task_id>/exports')
@login_required
def task_exports(task_id):
    task = SearchTask.query.get_or_404(task_id)
    exports = Export.query.filter_by(task_id=task_id).order_by(Export.created_at.desc()).all()
    return render_template('main/exports.html', task=task, exports=exports)

@bp.route('/task/<int:task_id>/export', methods=['GET'])
@login_required
def export_task_results(task_id):
    task = SearchTask.query.get_or_404(task_id)
    
    # Если есть готовый файл - отдаем его
    if task.result_file and os.path.exists(os.path.join(current_app.root_path, '..', task.result_file)):
        return send_file(
            os.path.join(current_app.root_path, '..', task.result_file),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'search_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        )
    
    # Получаем результаты из БД
    results = AnalysisResult.query.filter_by(task_id=task_id).all()
    if not results:
        flash('No results found', 'error')
        return redirect(url_for('main.task_results', task_id=task_id))
    
    # Создаем Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Преобразуем в DataFrame
        df = pd.DataFrame([r.to_dict() for r in results])
        
        # Записываем с форматированием
        df.to_excel(writer, index=False)
        
        # Получаем рабочий лист
        worksheet = writer.sheets['Sheet1']
        
        # Форматирование
        worksheet.row_dimensions[1].height = 30  # Заголовок
        for i in range(2, len(df) + 2):
            worksheet.row_dimensions[i].height = 75
        
        for column in worksheet.columns:
            max_length = 0
            for cell in column:
                try:
                    max_length = max(max_length, len(str(cell.value)))
                except:
                    pass
            adjusted_width = min(max_length + 2, 150)
            worksheet.column_dimensions[column[0].column_letter].width = adjusted_width
            
            # Форматирование ячеек
            for cell in column:
                cell.alignment = openpyxl.styles.Alignment(
                    wrap_text=True,
                    vertical='top'
                )
    
    output.seek(0)
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'analysis_results_{datetime.now().strftime("%Y%m%d")}.xlsx'
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

@bp.route('/parser')
@login_required
def parser():
    return render_template('main/parser.html')

@bp.route('/social-media')
@login_required
def social_media_parser():
    return render_template('main/social_media_parser.html')