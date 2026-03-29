from flask import Blueprint, request, jsonify
from server.app.models.page_text import PageText

texts = Blueprint("texts", __name__, url_prefix="/api/texts")

@texts.get("/page/<page>")
def get_texts_by_page(page: str):
    lang = request.args.get("lang", "en")  # /texts/page/home?lang=uk

    rows = PageText.query.filter_by(page=page, language=lang).all()

    if not rows:
        return jsonify({"error": "No texts found"}), 404

    return jsonify({row.key: row.value for row in rows})

@texts.get("/key/<key>")
def get_text_by_key(key: str):
    lang = request.args.get("lang", "en")  # /texts/key/hero_title?lang=uk

    row = PageText.query.filter_by(key=key, language=lang).first()

    if not row:
        return jsonify({"error": "Text not found"}), 404

    return jsonify({row.key: row.value})