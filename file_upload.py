import os
from datetime import datetime
from flask import jsonify, request
from werkzeug.utils import secure_filename as secure_filename_function
from flask_login import login_required
from app import app

@app.route('/admin/upload/file', methods=['POST'])
@login_required
def upload_file():
    """Upload general files like CV, documents, etc."""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file part'}), 400
        
    file = request.files['file']
    file_type = request.form.get('type', 'document')  # Default to document type
    
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No selected file'}), 400
        
    # Check file extension for allowed types
    allowed_extensions = {
        'cv': {'pdf', 'doc', 'docx'},
        'document': {'pdf', 'doc', 'docx', 'txt', 'rtf'},
        'image': {'jpg', 'jpeg', 'png', 'gif'}
    }
    
    extension = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    
    if extension not in allowed_extensions.get(file_type, {'pdf', 'doc', 'docx'}):
        return jsonify({
            'success': False, 
            'message': f'File type not allowed. Allowed types: {", ".join(allowed_extensions.get(file_type, ["pdf", "doc", "docx"]))}'
        }), 400
    
    try:
        # Secure save the file
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        secure_filename = f"{timestamp}_{secure_filename_function(file.filename)}"
        
        # Create uploads directory if it doesn't exist
        uploads_dir = os.path.join('static', 'uploads')
        if not os.path.exists(uploads_dir):
            os.makedirs(uploads_dir)
            
        file_path = os.path.join(uploads_dir, secure_filename)
        file.save(file_path)
        
        # Return file URL and success status
        file_url = f"/static/uploads/{secure_filename}"
        
        return jsonify({
            'success': True,
            'file_url': file_url,
            'file_name': secure_filename
        })
    except Exception as e:
        app.logger.error(f"Error uploading file: {str(e)}")
        return jsonify({
            'success': False, 
            'message': f'Error uploading file: {str(e)}'
        }), 500