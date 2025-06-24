# Make sure you have these packages installed:
# pip install Flask==2.3.3 Werkzeug==2.3.7 PyPDF2==3.0.1 python-docx==0.8.11 requests==2.31.0 Flask-WTF==1.1.1 python-dotenv==1.0.0

from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, jsonify, make_response
import os
import uuid
import csv
import io
import json
from datetime import datetime
from werkzeug.utils import secure_filename

from services.job_analyzer import JobAnalyzer
from services.resume_processor import ResumeProcessor
from services.candidate_evaluator import CandidateEvaluator
from utils.file_utils import allowed_file, create_directories, save_results_to_csv
from config import UPLOAD_FOLDER, ALLOWED_EXTENSIONS, SECRET_KEY, GOOGLE_API_KEY

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  
app.secret_key = SECRET_KEY

# Create necessary directories
create_directories([
    os.path.join(UPLOAD_FOLDER, 'job_descriptions'),
    os.path.join(UPLOAD_FOLDER, 'resumes'),
    os.path.join(UPLOAD_FOLDER, 'results'),
    os.path.join(UPLOAD_FOLDER, 'one_pager_temp') # For temporary 1-pager uploads
])

# Initialize services
job_analyzer = JobAnalyzer(GOOGLE_API_KEY)
resume_processor = ResumeProcessor() # resume_processor instance will be used for 1-pager
candidate_evaluator = CandidateEvaluator(GOOGLE_API_KEY)

# Session data storage (in-memory for demo purposes)
# In production, this should be replaced with a database
session_storage = {}

# Add context processor for current year
@app.context_processor
def inject_now():
    return {'now': datetime.now}

@app.route('/')
def index():
    """Render the home page"""
    return render_template('index.html')

@app.route('/job_description', methods=['GET', 'POST'])
def job_description():
    """Handle job description input"""
    if request.method == 'POST':
        # Get job description from form
        job_text = request.form.get('job_text', '')
        session_id = request.form.get('session_id', str(uuid.uuid4()))
        
        if not job_text:
            flash('Please enter a job description', 'danger')
            return redirect(request.url)
        
        # Create session directories
        session_dir = os.path.join(UPLOAD_FOLDER, session_id)
        job_dir = os.path.join(session_dir, 'job_descriptions')
        os.makedirs(job_dir, exist_ok=True)
        
        # Save job description to a text file
        job_filename = f"job_description_{session_id}.txt"
        job_path = os.path.join(job_dir, job_filename)
        with open(job_path, 'w', encoding='utf-8') as f:
            f.write(job_text)
        
        # Store session data
        if session_id not in session_storage:
            session_storage[session_id] = {}
        
        session_storage[session_id]['job_path'] = job_path
        session_storage[session_id]['job_description'] = job_text
        
        # Process job description to generate criteria
        try:
            criteria = job_analyzer.generate_criteria(job_text)
            session_storage[session_id]['criteria'] = criteria
            
            # Debug: Print session data
            print("Session data after job description processing:")
            print(f"Session ID: {session_id}")
            print(f"Job Description: {job_text[:50]}...")
            print(f"Criteria: {criteria}")
            
            # Check if this is an AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'status': 'success',
                    'session_id': session_id,
                    'criteria': criteria,
                    'redirect': url_for('set_criteria')
                })
            
            # For regular form submissions, redirect to criteria page
            return redirect(url_for('set_criteria', session_id=session_id))
        except Exception as e:
            flash(f'Error analyzing job description: {str(e)}', 'danger')
            return redirect(request.url)
    
    return render_template('job_description.html')

@app.route('/criteria', methods=['GET', 'POST'])
def set_criteria():
    """Handle setting priorities for evaluation criteria"""
    session_id = request.args.get('session_id') or request.form.get('session_id')
    
    if not session_id or session_id not in session_storage:
        flash('Please enter a job description first', 'warning')
        return redirect(url_for('job_description'))
    
    session_data = session_storage[session_id]
    
    if 'job_description' not in session_data:
        flash('Please enter a job description first', 'warning')
        return redirect(url_for('job_description'))
    
    if 'criteria' not in session_data:
        # If we have a job description but no criteria, try to generate them
        try:
            criteria = job_analyzer.generate_criteria(session_data['job_description'])
            session_data['criteria'] = criteria
        except Exception as e:
            flash(f'Error analyzing job description: {str(e)}', 'danger')
            return redirect(url_for('job_description'))
    
    criteria = session_data['criteria']
    
    if request.method == 'POST':
        # Get selected criteria and their priorities
        selected_criteria = []
        priorities = {}
        
        for criterion in criteria:
            checkbox_key = f'criterion_{criterion.replace(" ", "_")}'
            priority_key = f'priority_{criterion.replace(" ", "_")}'
            
            if checkbox_key in request.form:
                selected_criterion = criterion
                selected_criteria.append(selected_criterion)
                
                if priority_key in request.form:
                    try:
                        priority = int(request.form[priority_key])
                        if 1 <= priority <= 10:
                            priorities[selected_criterion] = priority
                        else:
                            flash(f'Priority for {selected_criterion} must be between 1 and 10', 'warning')
                            return redirect(url_for('set_criteria', session_id=session_id))
                    except ValueError:
                        flash(f'Invalid priority value for {selected_criterion}', 'warning')
                        return redirect(url_for('set_criteria', session_id=session_id))
        
        if not selected_criteria:
            flash('Please select at least one criterion', 'warning')
            return redirect(url_for('set_criteria', session_id=session_id))
        
        if len(priorities) != len(selected_criteria):
            flash('Please set priorities for all selected criteria', 'warning')
            return redirect(url_for('set_criteria', session_id=session_id))
        
        # Store selected criteria and priorities in session
        session_data['selected_criteria'] = selected_criteria
        session_data['priorities'] = priorities
        
        # Debug: Print session data
        print("Session data after criteria selection:")
        print(f"Session ID: {session_id}")
        print(f"Selected Criteria: {selected_criteria}")
        print(f"Priorities: {priorities}")
        
        # Check if this is an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'status': 'success',
                'session_id': session_id,
                'selected_criteria': selected_criteria,
                'priorities': priorities,
                'redirect': url_for('upload_resumes', session_id=session_id)
            })
        
        # For regular form submissions, redirect to upload resumes page
        return redirect(url_for('upload_resumes', session_id=session_id))
    
    return render_template('criteria.html', criteria=criteria, session_id=session_id)

# UPLOAD_FOLDER and ALLOWED_EXTENSIONS are now taken from config.py at the top
# session_storage is already defined globally

@app.route('/upload_resumes', methods=['GET', 'POST'])
def upload_resumes():
    """Handle resume uploads"""
    session_id = request.args.get('session_id') or request.form.get('session_id')

    if not session_id or session_id not in session_storage:
        flash('Please enter a job description first', 'warning')
        return redirect(url_for('job_description'))

    session_data = session_storage[session_id]

    if 'job_description' not in session_data:
        flash('Please enter a job description first', 'warning')
        return redirect(url_for('job_description'))

    if 'selected_criteria' not in session_data or 'priorities' not in session_data:
        flash('Please set criteria priorities first', 'warning')
        return redirect(url_for('set_criteria', session_id=session_id))

    if request.method == 'POST':
        if 'resumes' not in request.files:
            flash('No resume files provided', 'danger')
            return redirect(url_for('upload_resumes', session_id=session_id))

        resume_files = request.files.getlist('resumes')
        if not resume_files or resume_files[0].filename == '':
            flash('No resume files selected', 'danger')
            return redirect(url_for('upload_resumes', session_id=session_id))

        session_dir = os.path.join(app.config['UPLOAD_FOLDER'], session_id)
        resume_dir = os.path.join(session_dir, 'resumes')
        os.makedirs(resume_dir, exist_ok=True)

        resume_paths = []
        # Use ALLOWED_EXTENSIONS from config for consistency
        for resume_file in resume_files:
            if resume_file and allowed_file(resume_file.filename, ALLOWED_EXTENSIONS):
                filename = secure_filename(resume_file.filename)
                path = os.path.join(resume_dir, filename)
                resume_file.save(path)
                resume_paths.append(path)

        if not resume_paths:
            flash('No valid resume files uploaded. Allowed types: PDF, DOC, DOCX, TXT.', 'danger')
            return redirect(url_for('upload_resumes', session_id=session_id))

        session_data['resume_paths'] = resume_paths
        job_description = session_data['job_description']
        selected_criteria = session_data['selected_criteria']
        priorities = session_data['priorities']

        processed_resumes = {}
        for resume_path in resume_paths:
            candidate_name = os.path.basename(resume_path).split('.')[0]
            resume_text = resume_processor.extract_text(resume_path)
            if not resume_text.strip() or resume_text.startswith("Error extracting"):
                flash(f'{candidate_name} resume is empty or unreadable.', 'warning')
                continue
            processed_resumes[candidate_name] = resume_text

        if not processed_resumes:
            flash('No readable resumes processed.', 'danger')
            return redirect(url_for('upload_resumes', session_id=session_id))

        try:
            results = candidate_evaluator.evaluate_candidates(
                job_description,
                selected_criteria,
                priorities,
                processed_resumes
            )
            session_data['results'] = results
            results_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'results', session_id)
            os.makedirs(results_dir, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = os.path.join(results_dir, f'evaluation_results_{timestamp}.csv')
            sorted_results = sorted(
                [(candidate, data) for candidate, data in results.items()],
                key=lambda x: x[1]['overall_score'],
                reverse=True
            )
            save_results_to_csv(sorted_results, priorities, output_file)
            session_data['results_file'] = output_file

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'status': 'success',
                    'session_id': session_id,
                    'redirect': url_for('show_results', session_id=session_id)
                })
            return redirect(url_for('show_results', session_id=session_id))
        except Exception as e:
            flash(f'Error evaluating candidates: {str(e)}', 'danger')
            return redirect(url_for('upload_resumes', session_id=session_id))

    return render_template(
        'upload_resumes.html',
        session_id=session_id,
        selected_criteria=session_data.get('selected_criteria', []),
        priorities=session_data.get('priorities', {})
    )

@app.route('/results')
def show_results():
    """Display evaluation results"""
    session_id = request.args.get('session_id')
    
    if not session_id or session_id not in session_storage:
        flash('Please complete the evaluation process first', 'warning')
        return redirect(url_for('job_description'))
    
    session_data = session_storage[session_id]
    
    if 'results' not in session_data:
        flash('Please complete the evaluation process first', 'warning')
        return redirect(url_for('job_description'))
    
    results = session_data['results']
    priorities = session_data.get('priorities', {})
    criteria = session_data.get('selected_criteria', [])
    
    sorted_results = sorted(
        [(candidate, data) for candidate, data in results.items()],
        key=lambda x: x[1]['overall_score'],
        reverse=True
    )
    
    for candidate, data in sorted_results:
        if 'justifications' not in data:
            data['justifications'] = {}
        for criterion in criteria:
            if criterion not in data['justifications']:
                data['justifications'][criterion] = "No specific justification provided."
    
    return render_template(
        'results.html',
        results=sorted_results,
        priorities=priorities,
        criteria=criteria,
        results_file=session_data.get('results_file', ''),
        session_id=session_id
    )

@app.route('/download_results')
def download_results():
    """Download basic results as CSV"""
    session_id = request.args.get('session_id')
    if not session_id or session_id not in session_storage or 'results_file' not in session_storage[session_id]:
        flash('No results available to download', 'warning')
        return redirect(url_for('index'))
    
    results_file = session_storage[session_id]['results_file']
    if not os.path.exists(results_file):
        flash('Results file not found', 'warning')
        return redirect(url_for('index'))
    
    return send_file(results_file, as_attachment=True, download_name='resume_evaluation_results.csv', mimetype='text/csv')

@app.route('/download_detailed_csv')
def download_detailed_csv():
    """Download detailed results as CSV including justifications"""
    session_id = request.args.get('session_id')
    if not session_id or session_id not in session_storage or 'results' not in session_storage[session_id]:
        flash('No results available to download', 'warning')
        return redirect(url_for('index'))
    
    session_data = session_storage[session_id]
    results = session_data['results']
    priorities = session_data.get('priorities', {})
    criteria = session_data.get('selected_criteria', [])
    
    sorted_results = sorted([(c, d) for c, d in results.items()], key=lambda x: x[1]['overall_score'], reverse=True)
    
    output = io.StringIO()
    writer = csv.writer(output)
    header = ['Candidate', 'Overall Score (%)'] + [f"{cr} (Score)" for cr in criteria] + [f"{cr} (Justification)" for cr in criteria]
    writer.writerow(header)
    
    for candidate, data in sorted_results:
        row = [candidate, f"{data['overall_score']:.2f}"]
        for cr in criteria: row.append(data['criteria_scores'].get(cr, 0))
        for cr in criteria: row.append(data['justifications'].get(cr, "No justification provided."))
        writer.writerow(row)
        
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=detailed_evaluation_results.csv"
    response.headers["Content-type"] = "text/csv"
    return response

@app.route('/download_detailed_excel')
def download_detailed_excel():
    """Download comprehensive results as Excel file including all ratings and justifications"""
    session_id = request.args.get('session_id')
    if not session_id or session_id not in session_storage or 'results' not in session_storage[session_id]:
        flash('No results available to download', 'warning')
        return redirect(url_for('index'))
    
    session_data = session_storage[session_id]
    try:
        import pandas as pd
        from io import BytesIO
        
        results = session_data['results']
        priorities = session_data.get('priorities', {})
        criteria = session_data.get('selected_criteria', [])
        job_description = session_data.get('job_description', 'Not available')
        
        sorted_results = sorted([(c, d) for c, d in results.items()], key=lambda x: x[1]['overall_score'], reverse=True)
        
        summary_data = {'Candidate': [], 'Overall Score (%)': [], 'Rank': []}
        for criterion in criteria:
            summary_data[f"{criterion} (Score)"] = []
            summary_data[f"{criterion} (Priority)"] = []
        
        for i, (candidate, data) in enumerate(sorted_results):
            summary_data['Candidate'].append(candidate)
            summary_data['Overall Score (%)'].append(f"{data['overall_score']:.2f}")
            summary_data['Rank'].append(i + 1)
            for criterion in criteria:
                summary_data[f"{criterion} (Score)"].append(data['criteria_scores'].get(criterion, 0))
                summary_data[f"{criterion} (Priority)"].append(priorities.get(criterion, 5))
        
        detailed_data = {'Candidate': [], 'Criterion': [], 'Score': [], 'Priority': [], 'Justification': []}
        for candidate, data in sorted_results:
            for criterion in criteria:
                detailed_data['Candidate'].append(candidate)
                detailed_data['Criterion'].append(criterion)
                detailed_data['Score'].append(data['criteria_scores'].get(criterion, 0))
                detailed_data['Priority'].append(priorities.get(criterion, 5))
                detailed_data['Justification'].append(data['justifications'].get(criterion, "No justification provided."))
        
        output_excel = BytesIO()
        with pd.ExcelWriter(output_excel, engine='xlsxwriter') as writer:
            summary_df = pd.DataFrame(summary_data)
            detailed_df = pd.DataFrame(detailed_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False, startrow=4) # Start data later for title
            detailed_df.to_excel(writer, sheet_name='Detailed Justifications', index=False)
            
            workbook = writer.book
            summary_sheet = writer.sheets['Summary']
            detailed_sheet = writer.sheets['Detailed Justifications']
            
            header_format = workbook.add_format({'bold': True, 'text_wrap': True, 'valign': 'top', 'fg_color': '#D7E4BC', 'border': 1})
            for col_num, value in enumerate(summary_df.columns.values): summary_sheet.write(4, col_num, value, header_format) # Headers at row 4
            for col_num, value in enumerate(detailed_df.columns.values): detailed_sheet.write(0, col_num, value, header_format)
            
            summary_sheet.set_column(0, 0, 20); summary_sheet.set_column(1, 1, 15); summary_sheet.set_column(2, 2, 10)
            summary_sheet.set_column(3, len(summary_df.columns), 15)
            detailed_sheet.set_column(0, 0, 20); detailed_sheet.set_column(1, 1, 30); detailed_sheet.set_column(2, 3, 10)
            detailed_sheet.set_column(4, 4, 50, workbook.add_format({'text_wrap': True}))

            # Conditional formatting (simplified for brevity, apply as in original)
            score_formats = {
                'high': workbook.add_format({'bg_color': '#C6EFCE', 'font_color': '#006100'}),
                'medium': workbook.add_format({'bg_color': '#FFEB9C', 'font_color': '#9C5700'}),
                'low': workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'})
            }
            # Apply to summary sheet score columns (starting from data row 5)
            for i, col_name in enumerate(summary_df.columns):
                if "(Score)" in col_name:
                    col_letter = chr(65 + i)
                    data_end_row = 4 + len(summary_df)
                    summary_sheet.conditional_format(f'{col_letter}6:{col_letter}{data_end_row+1}', {'type': 'cell', 'criteria': '>=', 'value': 8, 'format': score_formats['high']})
                    summary_sheet.conditional_format(f'{col_letter}6:{col_letter}{data_end_row+1}', {'type': 'cell', 'criteria': 'between', 'minimum': 6, 'maximum': 7.99, 'format': score_formats['medium']})
                    summary_sheet.conditional_format(f'{col_letter}6:{col_letter}{data_end_row+1}', {'type': 'cell', 'criteria': '<', 'value': 6, 'format': score_formats['low']})
            # Apply to detailed sheet score column C (starting from data row 2)
            detailed_sheet.conditional_format(f'C2:C{len(detailed_df)+1}', {'type': 'cell', 'criteria': '>=', 'value': 8, 'format': score_formats['high']})
            detailed_sheet.conditional_format(f'C2:C{len(detailed_df)+1}', {'type': 'cell', 'criteria': 'between', 'minimum': 6, 'maximum': 7.99, 'format': score_formats['medium']})
            detailed_sheet.conditional_format(f'C2:C{len(detailed_df)+1}', {'type': 'cell', 'criteria': '<', 'value': 6, 'format': score_formats['low']})


            pd.DataFrame({'Job Description': [job_description]}).to_excel(writer, sheet_name='Job Description', index=False)
            writer.sheets['Job Description'].set_column(0, 0, 100, workbook.add_format({'text_wrap': True}))
            pd.DataFrame({'Criterion': list(priorities.keys()), 'Priority (1-10)': list(priorities.values())}).to_excel(writer, sheet_name='Criteria Priorities', index=False)
            writer.sheets['Criteria Priorities'].set_column(0, 0, 40); writer.sheets['Criteria Priorities'].set_column(1, 1, 15)
            
            summary_sheet.merge_range('A1:C1', 'Resume Evaluation Results', workbook.add_format({'bold': True, 'font_size': 14, 'align': 'center'}))
            summary_sheet.write(1, 0, f'Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
            summary_sheet.write(2, 0, f'Total Candidates: {len(sorted_results)}')
            summary_sheet.write(3, 0, f'Total Criteria: {len(criteria)}')

        output_excel.seek(0)
        response = make_response(output_excel.getvalue())
        response.headers["Content-Disposition"] = "attachment; filename=detailed_resume_evaluation.xlsx"
        response.headers["Content-type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        return response
        
    except ImportError:
        flash('Excel export requires pandas and xlsxwriter. Falling back to CSV.', 'warning')
        return redirect(url_for('download_detailed_csv', session_id=session_id))
    except Exception as e:
        flash(f'Error generating Excel file: {str(e)}', 'danger')
        return redirect(url_for('show_results', session_id=session_id))

@app.route('/api/session', methods=['GET', 'POST'])
def api_session():
    """API endpoint for session data"""
    if request.method == 'GET':
        session_id = request.args.get('session_id')
        if not session_id or session_id not in session_storage:
            return jsonify({'status': 'error', 'message': 'Session not found'})
        return jsonify({'status': 'success', 'session_id': session_id, 'data': session_storage[session_id]})
    
    elif request.method == 'POST':
        if not request.is_json: return jsonify({'status': 'error', 'message': 'Invalid request format'})
        data = request.get_json()
        session_id = data.get('session_id', str(uuid.uuid4()))
        if session_id not in session_storage: session_storage[session_id] = {}
        for key, value in data.items():
            if key != 'session_id': session_storage[session_id][key] = value
        return jsonify({'status': 'success', 'session_id': session_id})

# New route for 1-pager resume creator
@app.route('/one-pager', methods=['GET', 'POST'])
def one_pager_creator():
    if request.method == 'POST':
        if 'resume_file' not in request.files:
            flash('No resume file provided', 'danger')
            return redirect(request.url)
        
        file = request.files['resume_file']
        if file.filename == '':
            flash('No resume file selected', 'danger')
            return redirect(request.url)

        # Use ALLOWED_EXTENSIONS from config.py
        if file and allowed_file(file.filename, ALLOWED_EXTENSIONS):
            temp_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'one_pager_temp')
            # os.makedirs(temp_dir, exist_ok=True) # Already created at app start

            filename = secure_filename(file.filename)
            temp_file_path = os.path.join(temp_dir, filename)
            
            try:
                file.save(temp_file_path)
                docx_stream = resume_processor.generate_one_pager_docx(temp_file_path)
                
                return send_file(
                    docx_stream,
                    as_attachment=True,
                    download_name='anonymized_one_pager.docx',
                    mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                )
            except ValueError as e:
                flash(str(e), 'danger')
            except Exception as e:
                app.logger.error(f"Error in one_pager_creator: {e}", exc_info=True)
                flash(f'An error occurred while generating the 1-pager: {str(e)}', 'danger')
            finally:
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path) # Clean up the temporary file
            return redirect(request.url)
        else:
            flash(f'Invalid file type. Allowed types are: {", ".join(ALLOWED_EXTENSIONS)}.', 'danger')
            return redirect(request.url)
            
    return render_template('one_pager_upload.html')


@app.errorhandler(413)
def request_entity_too_large(error):
    flash('File too large. Maximum file size is 50MB.', 'danger') # Updated to 50MB as per MAX_CONTENT_LENGTH
    # Redirect to previous page or a specific upload page
    if 'upload_resumes' in request.referrer:
        return redirect(url_for('upload_resumes')), 413
    elif 'one-pager' in request.referrer:
        return redirect(url_for('one_pager_creator')), 413
    return redirect(url_for('index')), 413


@app.errorhandler(500)
def internal_server_error(error):
    app.logger.error(f"Server Error: {error}", exc_info=True)
    flash('An internal server error occurred. Please try again later.', 'danger')
    return render_template('index.html'), 500

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_file(os.path.join(app.root_path, 'static', filename))

if __name__ == '__main__':
    app.run(debug=True)
