from flask import render_template, request, send_file, jsonify
from app.models import SearchTask, AnalysisResult
import pandas as pd
from datetime import datetime
import io

@bp.route('/task/<int:task_id>/results', methods=['GET'])
def task_results(task_id):
    task = SearchTask.query.get_or_404(task_id)
    results = AnalysisResult.query.filter_by(task_id=task_id).all()
    
    # Преобразуем результаты для отображения в таблице
    data = [{
        'company_name': r.company_name,
        'potential': r.potential,
        'sales_notes': r.sales_notes,
        'company_description': r.company_description,
        'revenue': r.revenue,
        'country': r.country,
        'website': r.website,
        'article_date': r.article_date.strftime('%Y-%m-%d') if r.article_date else 'N/A'
    } for r in results]
    
    return render_template('task/results.html', 
                         task=task, 
                         results=data,
                         min_potential=request.args.get('min_potential', 0, type=int))

@bp.route('/task/<int:task_id>/export', methods=['GET'])
def export_results(task_id):
    task = SearchTask.query.get_or_404(task_id)
    
    # Получаем параметры фильтрации
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    min_potential = request.args.get('min_potential', 0, type=int)
    
    # Базовый запрос
    query = AnalysisResult.query.filter_by(task_id=task_id)
    
    # Применяем фильтры
    if start_date:
        query = query.filter(AnalysisResult.article_date >= datetime.strptime(start_date, '%Y-%m-%d'))
    if end_date:
        query = query.filter(AnalysisResult.article_date <= datetime.strptime(end_date, '%Y-%m-%d'))
    if min_potential:
        query = query.filter(AnalysisResult.potential >= min_potential)
    
    results = query.order_by(AnalysisResult.article_date.desc()).all()
    
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