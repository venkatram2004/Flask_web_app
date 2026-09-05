from flask import Blueprint, request, jsonify, session
from models.transaction import (
    create_transaction, get_all_transactions,
    get_transaction_by_id, update_transaction, delete_transaction
)
from models.user import authenticate_user, create_user

api_bp = Blueprint('api', __name__, url_prefix='/api')


def login_required_json(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated


def admin_required_json(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role') != 'admin':
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)
    return decorated


# ---- AUTH ----
@api_bp.route('/auth/login', methods=['POST'])
def api_login():
    data = request.get_json()
    user = authenticate_user(data.get('username', '').strip(), data.get('password', '').strip())
    if user:
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']
        return jsonify({"id": user['id'], "username": user['username'], "role": user['role']})
    return jsonify({"error": "Invalid username or password"}), 401


@api_bp.route('/auth/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({"message": "Logged out"})


@api_bp.route('/auth/me', methods=['GET'])
@login_required_json
def api_me():
    return jsonify({
        "user_id": session.get('user_id'),
        "username": session.get('username'),
        "role": session.get('role')
    })


@api_bp.route('/auth/register', methods=['POST'])
def api_register():
    data = request.get_json()
    user_id, error = create_user(
        data.get('username', '').strip(),
        data.get('password', '').strip(),
        data.get('role', 'viewer').strip()
    )
    if error:
        return jsonify({"error": error}), 400
    return jsonify({"id": user_id}), 201


# ---- TRANSACTIONS ----
@api_bp.route('/transactions', methods=['GET'])
@login_required_json
def api_list_transactions():
    role = session.get('role')
    user_id = session.get('user_id')

    filters = {}
    if role in ('analyst', 'admin'):
        filters = {
            "type_": request.args.get('type'),
            "category": request.args.get('category'),
            "date_from": request.args.get('date_from'),
            "date_to": request.args.get('date_to'),
        }

    filter_user_id = None if role == 'admin' else user_id
    transactions = get_all_transactions(user_id=filter_user_id, **filters)
    return jsonify(transactions)


@api_bp.route('/transactions', methods=['POST'])
@login_required_json
@admin_required_json
def api_add_transaction():
    data = request.get_json()
    txn_id, errors = create_transaction(
        session['user_id'], data.get('amount'), data.get('type'),
        data.get('category'), data.get('date'), data.get('notes', '')
    )
    if errors:
        return jsonify({"errors": errors}), 400
    return jsonify({"id": txn_id}), 201


@api_bp.route('/transactions/<int:txn_id>', methods=['GET'])
@login_required_json
def api_get_transaction(txn_id):
    txn = get_transaction_by_id(txn_id)
    if not txn:
        return jsonify({"error": "Not found"}), 404
    return jsonify(txn)


@api_bp.route('/transactions/<int:txn_id>', methods=['PUT'])
@login_required_json
@admin_required_json
def api_update_transaction(txn_id):
    data = request.get_json()
    success, errors = update_transaction(
        txn_id, amount=data.get('amount'), type_=data.get('type'),
        category=data.get('category'), date=data.get('date'), notes=data.get('notes', '')
    )
    if not success:
        return jsonify({"errors": errors}), 400
    return jsonify({"message": "Updated"})


@api_bp.route('/transactions/<int:txn_id>', methods=['DELETE'])
@login_required_json
@admin_required_json
def api_delete_transaction(txn_id):
    success, error = delete_transaction(txn_id)
    if not success:
        return jsonify({"error": error}), 400
    return jsonify({"message": "Deleted"})

# ---- SUMMARY ----
@api_bp.route('/summary', methods=['GET'])
@login_required_json
def api_summary():
    role = session.get('role')
    user_id = session.get('user_id')
    filter_user_id = None if role == 'admin' else user_id

    transactions = get_all_transactions(user_id=filter_user_id)

    total_income = sum(t['amount'] for t in transactions if t['type'] == 'income')
    total_expense = sum(t['amount'] for t in transactions if t['type'] == 'expense')
    net_balance = total_income - total_expense

    category_totals = {}
    for t in transactions:
        if t['type'] == 'expense':
            category_totals[t['category']] = category_totals.get(t['category'], 0) + t['amount']

    monthly_totals = {}
    for t in transactions:
        month = t['date'][:7]
        if month not in monthly_totals:
            monthly_totals[month] = {"income": 0, "expense": 0}
        monthly_totals[month][t['type']] += t['amount']

    monthly_trend = [
        {"month": m, "income": v["income"], "expense": v["expense"]}
        for m, v in sorted(monthly_totals.items())
    ]

    return jsonify({
        "total_income": total_income,
        "total_expense": total_expense,
        "net_balance": net_balance,
        "category_breakdown": [{"category": k, "amount": v} for k, v in category_totals.items()],
        "monthly_trend": monthly_trend
    })