from flask import render_template, flash, redirect, url_for, request, current_app, send_file, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import JobSearchTask, JobSearchQuery
from app.forms.job_search import JobSearchForm
from app.tasks.job_search import start_job_search
# from app.routes.client import check_client_access  # закомментируем проверку клиента
from . import bp
import pandas as pd
import io
from datetime import datetime

# Создаем фейкового пользователя
class DummyUser:
    def __init__(self):
        self.client_id = 1  # фейковый client_id
        self.id = 1  # фейковый user_id
        self.is_authenticated = True
        self.is_active = True

def dummy_login_required(f):
    def wrapped(*args, **kwargs):
        global current_user
        current_user = DummyUser()
        return f(*args, **kwargs)
    return wrapped

@bp.route('/job_search', methods=['GET', 'POST'])
@dummy_login_required
def job_search():
    form = JobSearchForm()
    if form.validate_on_submit():
        # Create a new JobSearchTask
        task = JobSearchTask(
            status='pending',
            client_id=current_user.client_id,  # используем фейковый client_id
            search_phrase=form.search_phrase.data,
            days_old=form.days_old.data,
            max_jobs=form.max_jobs.data
        )
        db.session.add(task)
        db.session.flush()

        # Create JobSearchQuery entries for each selected source
        selected_sources = form.get_selected_sources()  # используем метод из формы
        for source in selected_sources:
            query = JobSearchQuery(
                task_id=task.id,
                source=source,
                parameters={
                    'search_phrase': form.search_phrase.data,
                    'days_old': form.days_old.data,
                    'max_jobs': form.max_jobs.data
                }
            )
            db.session.add(query)

        db.session.commit()

        # Start the Celery task
        start_job_search.delay(task.id)

        flash(f'Job search task {task.id} has been started.', 'success')
        return redirect(url_for('main.view_task', task_id=task.id))

    return render_template('main/job_search.html', form=form)

@bp.route('/view_task/<int:task_id>')
@login_required
def view_task(task_id):
    task = JobSearchTask.query.get_or_404(task_id)
    
    # Use the unified access check
    client, error = check_client_access(task.client_id)
    if error:
        flash(error, 'error')
        return redirect(url_for('main.index'))
        
    return render_template('main/view_task.html', task=task)

@bp.route('/task/<int:task_id>/download')
@login_required
def download_task_results(task_id):
    """Download task results as Excel file"""
    task = JobSearchTask.query.get_or_404(task_id)
    
    try:
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            results_data = []
            for result in task.results:
                # Get analysis data
                analysis = result.analysis or {}
                
                row = {
                    'Title': result.job_data.get('Title', ''),
                    'Company': result.job_data.get('Company', ''),
                    'Location': result.job_data.get('Location', ''),
                    'Source': result.source,
                    'URL': result.job_data.get('URL', ''),
                    'Posted Date': result.job_data.get('Posted', ''),
                    'Notes': analysis.get('notes', '')
                }
                results_data.append(row)
            
            # Create DataFrame and sort by signal strength
            df = pd.DataFrame(results_data)
            
            # Write to Excel with formatting
            df.to_excel(writer, index=False, sheet_name='Job Results')
            
            # Format worksheet
            worksheet = writer.sheets['Job Results']
            
            # Format columns
            for idx, col in enumerate(df.columns):
                max_length = max(df[col].astype(str).apply(len).max(), len(col))
                worksheet.column_dimensions[chr(65 + idx)].width = min(max_length + 2, 50)
            
            # Format header
            for cell in worksheet[1]:
                cell.style = 'Headline 2'

        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'job_search_results_{task.id}_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx'
        )

    except Exception as e:
        current_app.logger.error(f"Error generating Excel file: {str(e)}")
        flash('Error generating Excel file.', 'error')
        return redirect(url_for('main.view_task', task_id=task_id))

@bp.route('/api/search', methods=['POST'])
@login_required
def job_search():
    # Get search parameters
    search_params = request.json
    enrichment_config = search_params.get('enrichment_config', {})
    
    # Create search task
    task = JobSearchTask(
        user_id=current_user.id,
        status='pending',
        enrichment_config=enrichment_config  # Store config in task
    )
    db.session.add(task)
    db.session.commit()
    
    # Start celery task
    start_job_search.delay(task.id)
    
    return jsonify({'task_id': task.id}) 