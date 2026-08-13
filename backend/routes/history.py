import json
import csv
import io
from flask import Blueprint, request, jsonify, Response
from werkzeug.utils import secure_filename

from services.db_service import get_movie_analysis, save_movie_analysis, get_all_movie_analysis, delete_movie_analysis

history_bp = Blueprint('history', __name__)

def get_json_data():
    return request.get_json(silent=True) or {}

@history_bp.route('/update_interpretation', methods=['POST'])
def update_interpretation():
    data         = get_json_data()
    mode         = data.get('mode', 'bigram')
    db_key       = f"{data.get('title')}_{mode}_k{data.get('num_topics')}"
    topic_id     = data.get('topic_id')
    custom_label = data.get('custom_label', '')
    notes        = data.get('notes', '')

    try:
        result_data = get_movie_analysis(db_key)
        if result_data:
            if 'interpretations' not in result_data:
                result_data['interpretations'] = {}
            result_data['interpretations'][topic_id] = {"custom_label": custom_label, "notes": notes}
            
            # Save it back (this will trigger ON CONFLICT DO UPDATE)
            save_movie_analysis(db_key, result_data)
            return jsonify({"status": "success", "data": result_data})

        return jsonify({"error": "Data analisis belum tersimpan"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@history_bp.route('/saved_movies', methods=['GET'])
def get_saved_movies():
    try:
        rows = get_all_movie_analysis()
        result = []
        for row in rows:
            id_title = row['id_title']
            rd = row['result_data']
            
            optimal_k = None
            is_empty = False
            try:
                k_results = rd.get('optimal_k_results')
                if k_results:
                    best = max(k_results, key=lambda x: x.get('score', 0))
                    optimal_k = best.get('k')
                
                # Check if topics meet the minimum threshold of valid words
                topics = rd.get('topics', {})
                total_words = 0
                for t_name, t_data in topics.items():
                    total_words += len(t_data.get('words', []))
                
                # Syarat minimum yang lebih ketat: rata-rata minimal 3 kata kunci valid per topik.
                k_value = len(topics)
                if k_value > 0 and total_words < (k_value * 3):
                    is_empty = True
            except Exception:
                pass
            result.append({"id_title": id_title, "optimal_k": optimal_k, "is_empty": is_empty})

        return jsonify({"status": "success", "data": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@history_bp.route('/saved_movies/<title>', methods=['GET'])
def get_saved_movie_detail(title):
    try:
        data = get_movie_analysis(title)
        if data:
            return jsonify({"status": "success", "data": data})
        return jsonify({"error": "Data tidak ditemukan"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@history_bp.route('/delete_movie/<title>', methods=['DELETE'])
def delete_movie(title):
    try:
        delete_movie_analysis(title)
        return jsonify({"status": "success", "message": "Data berhasil dihapus"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@history_bp.route('/export_csv/<title>', methods=['GET'])
def export_csv(title):
    try:
        result_data = get_movie_analysis(title)

        if not result_data:
            return jsonify({"error": "Data tidak ditemukan"}), 404

        doc_distributions = result_data.get('document_distributions', [])
        interpretations  = result_data.get('interpretations', {})
        topics           = result_data.get('topics', {})

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID Dokumen', 'Teks Ulasan', 'Topik Dominan', 'Label Topik', 'Probabilitas'])

        for doc in doc_distributions:
            dom   = doc.get('dominant_topic', '')
            label = (interpretations.get(dom, {}).get('custom_label')
                     or topics.get(dom, {}).get('auto_label', ''))
            writer.writerow([
                doc.get('doc_id', ''),
                doc.get('text', ''),
                dom,
                label,
                round(doc.get('probability', 0), 4)
            ])

        output.seek(0)
        safe_title = secure_filename(title)
        return Response(
            output.getvalue(),
            mimetype='text/csv; charset=utf-8',
            headers={
                'Content-Disposition': f'attachment; filename="{safe_title}_hasil_analisis.csv"'
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
