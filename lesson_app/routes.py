import json
import os
import uuid
import datetime
from flask import render_template, request, Response, flash, redirect, url_for, Blueprint, abort
from weasyprint import HTML, CSS
from flask_login import current_user, login_user, logout_user, login_required
from urllib.parse import urlparse
from lesson_app import db
from lesson_app.forms import LoginForm, RegistrationForm, GameForm
from lesson_app.models import User
from werkzeug.utils import secure_filename

bp = Blueprint('routes', __name__)

# --- נתיבים וקבצים קבועים ---
PROJECT_ROOT   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAMES_JSON_PATH = os.path.join(PROJECT_ROOT, 'games.json')
UPLOAD_FOLDER   = os.path.join(PROJECT_ROOT, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------- עזרי קבצים/URI ----------
def file_uri(path: str | None) -> str | None:
    if not path:
        return None
    return 'file:///' + os.path.abspath(path).replace('\\', '/')

def resolve_image_path(val: str | None) -> str | None:
    if not val:
        return None
    v = str(val).strip()
    if v.startswith(('http://','https://','file:///')):
        return v
    if os.path.isabs(v) and os.path.exists(v):
        return file_uri(v)
    candidates = [
        os.path.join(UPLOAD_FOLDER, v),
        os.path.join(PROJECT_ROOT, v),
        os.path.join(PROJECT_ROOT, 'static', v),
    ]
    for p in candidates:
        if os.path.exists(p):
            return file_uri(p)
    return None

def augment_game_obj(obj: dict | None) -> dict | None:
    if obj is None:
        return None
    out = dict(obj)
    out['image_path'] = resolve_image_path(out.get('image'))
    return out

def ensure_game_ids(games_data: dict) -> bool:
    """נותן לכל משחק id ייחודי אם חסר (עוזר למחיקה בטוחה). מחזיר אם נעשה שינוי."""
    changed = False
    for cat in ('חימום','עיקרי','סיום'):
        for g in games_data.get(cat, []):
            if 'id' not in g:
                g['id'] = uuid.uuid4().hex
                changed = True
    return changed

# --- התחברות/התנתקות/בית ---
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('routes.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('שם משתמש או סיסמה לא נכונים')
            return redirect(url_for('routes.login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('routes.home')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('routes.login'))

@bp.route('/')
@login_required
def home():
    with open(GAMES_JSON_PATH, 'r', encoding='utf-8') as f:
        games_data = json.load(f)
    display_data = {
        "חימום": [item['title'] for item in games_data['חימום']],
        "עיקרי": [item['title'] for item in games_data['עיקרי']],
        "סיום":  [item['title'] for item in games_data['סיום']]
    }
    footer_text = "כל הזכויות שמורות לעמותת ניקה ספורט וקהילה. אין לעשות שימוש בתוכן ללא אישור מראש ובכתב מהעמותה."
    return render_template('index.html', data=display_data, footer_text=footer_text)

# --- ניהול משתמשים (מוגן) ---
@bp.route('/manage_users', methods=['GET', 'POST'])
@login_required
def manage_users():
    if current_user.username != 'Hay':
        abort(403)
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('המאמן נוסף בהצלחה!')
        return redirect(url_for('routes.manage_users'))
    users = User.query.all()
    return render_template('manage_users.html', title='ניהול משתמשים', form=form, users=users)

@bp.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.username != 'Hay':
        abort(403)
    user_to_delete = User.query.get_or_404(user_id)
    if user_to_delete.id == current_user.id:
        flash('אינך יכול למחוק את המשתמש של עצמך.')
        return redirect(url_for('routes.manage_users'))
    db.session.delete(user_to_delete)
    db.session.commit()
    flash('המאמן נמחק בהצלחה.')
    return redirect(url_for('routes.manage_users'))

# --- ניהול משחקים (מוגן): הוספה + רשימה עם "מחק" ---
@bp.route('/manage_games', methods=['GET', 'POST'])
@login_required
def manage_games():
    if current_user.username != 'Hay':
        abort(403)

    with open(GAMES_JSON_PATH, 'r', encoding='utf-8') as f:
        games_data = json.load(f)

    # ודא שלכל המשחקים יש id
    if ensure_game_ids(games_data):
        with open(GAMES_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(games_data, f, ensure_ascii=False, indent=2)

    form = GameForm()
    if form.validate_on_submit():
        new_game = {
            "id": uuid.uuid4().hex,  # מזהה ייחודי למחיקה בטוחה
            "title": form.title.data,
            "bullets": [line for line in form.bullets.data.splitlines() if line.strip()],
            "image": ""
        }

        if form.image.data:
            image_file = form.image.data
            filename = secure_filename(image_file.filename)
            save_path = os.path.join(UPLOAD_FOLDER, filename)
            image_file.save(save_path)
            new_game["image"] = filename  # נשמור רק שם קובץ

        games_data[form.category.data].append(new_game)

        with open(GAMES_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(games_data, f, ensure_ascii=False, indent=2)

        flash('המשחק נוסף בהצלחה!')
        return redirect(url_for('routes.manage_games'))

    return render_template('manage_games.html', games_data=games_data, form=form)

@bp.route('/delete_game', methods=['POST'])
@login_required
def delete_game():
    if current_user.username != 'Hay':
        abort(403)

    game_id  = request.form.get('game_id')
    category = request.form.get('category')  # "חימום" / "עיקרי" / "סיום"

    if not game_id or not category:
        flash('בקשת מחיקה לא תקינה.')
        return redirect(url_for('routes.manage_games'))

    with open(GAMES_JSON_PATH, 'r', encoding='utf-8') as f:
        games_data = json.load(f)

    lst = games_data.get(category, [])
    idx = next((i for i, g in enumerate(lst) if g.get('id') == game_id), None)

    if idx is None:
        flash('המשחק לא נמצא.')
        return redirect(url_for('routes.manage_games'))

    removed = lst.pop(idx)
    image_name = removed.get('image') or ''

    with open(GAMES_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(games_data, f, ensure_ascii=False, indent=2)

    # מחיקת קובץ תמונה אם לא בשימוש אצל משחקים אחרים
    if image_name:
        still_used = any(
            (g.get('image') == image_name)
            for cat in ('חימום','עיקרי','סיום')
            for g in games_data.get(cat, [])
        )
        if not still_used:
            img_path = os.path.join(UPLOAD_FOLDER, image_name)
            if os.path.exists(img_path):
                try:
                    os.remove(img_path)
                except OSError:
                    pass

    flash('המשחק נמחק בהצלחה.')
    return redirect(url_for('routes.manage_games'))

# --- יצירת PDF ---
@bp.route('/create_pdf', methods=['POST'])
@login_required
def create_pdf_route():
    with open(GAMES_JSON_PATH, 'r', encoding='utf-8') as f:
        games_data = json.load(f)

    warmup_title   = request.form.get('warmup')
    main_title     = request.form.get('main')
    cooldown_title = request.form.get('cooldown')

    warmup_obj   = augment_game_obj(next((i for i in games_data['חימום'] if i['title'] == warmup_title), None))
    main_obj     = augment_game_obj(next((i for i in games_data['עיקרי'] if i['title'] == main_title), None))
    cooldown_obj = augment_game_obj(next((i for i in games_data['סיום']  if i['title'] == cooldown_title), None))

    today_date = datetime.date.today().strftime("%d/%m/%Y")

    html_out = render_template(
        'pdf_template.html',
        warmup=warmup_obj,
        main=main_obj,
        cooldown=cooldown_obj,
        today_date=today_date,
        logo_path=file_uri(os.path.join(PROJECT_ROOT, 'logo.png'))
    )

    css_path = os.path.join(PROJECT_ROOT, 'lesson_app', 'static', 'pdf_style.css')
    base_url = PROJECT_ROOT

    pdf_bytes = HTML(string=html_out, base_url=base_url).write_pdf(
        stylesheets=[CSS(css_path)]
    )

    return Response(
        pdf_bytes,
        mimetype='application/pdf',
        headers={'Content-Disposition': 'attachment; filename=lesson_plan.pdf'}
    )
