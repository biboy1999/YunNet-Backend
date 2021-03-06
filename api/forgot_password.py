from datetime import timedelta, datetime
from time import time
from hashlib import sha256

from sanic import Blueprint
from sanic.response import json
from sanic_openapi import doc, api
from email.mime.text import MIMEText
from aiosmtplib.errors import SMTPRecipientsRefused

from Base import messages, SMTP, big5_encode
from Query import User
from Query.group import Group
from Query.token import Token

bp_forgot_passowrd = Blueprint("forgot-password")


class forgot_password_doc(api.API):
    consumes_content_type = "application/json"
    consumes_location = "body"
    consumes_required = True

    class consumes:
        username = doc.String("Username")

    consumes = doc.JsonBody(vars(consumes))

    class SuccessResp:
        code = 200
        description = "On success request"

        class model:
            message = doc.String("message")

        model = dict(vars(model))

    class FailResp:
        code = 401
        description = "On failed request"

        class model:
            message = doc.String("Error message")

        model = dict(vars(model))

    response = [SuccessResp, FailResp]


@forgot_password_doc
@bp_forgot_passowrd.route("/forgot-password", methods=["POST"])
async def bp_user_forgot_password(request):
    username = request.json["username"]
    # TODO recover jwt token
    
    # Token creation
    hexdigest = username + repr(time())
    hexdigest = sha256(hexdigest.encode()).hexdigest()
    recover_code = username + "_" + hexdigest

    group_list = await Group.get_user_group(username)
    if any(group["gid"] == 2 for group in group_list):
        return messages.NOT_REGISTERED

    # Insert to database
    uid = await User.get_user_id(username)
    if uid is None:
        return messages.USER_DOES_NOT_EXIST
    affect_row = await Token.add_token(uid, recover_code)
    if not affect_row:
        return messages.INTERNAL_SERVER_ERROR

    # Send mail
    try:
        mailaddr = "{0}@yuntech.edu.tw".format(username)
        await SMTP.send_recovery_mail(mailaddr, recover_code)
    except SMTPRecipientsRefused as e:
        return json({"message": e.recipients[0].message}, 500)
    return messages.OPERATION_SUCCESS


class forgot_password_verify_doc(api.API):
    consumes_content_type = "application/json"
    consumes_location = "body"
    consumes_required = True

    class consumes:
        password = doc.String("User's new password")

    consumes = doc.JsonBody(vars(consumes))

    class SuccessResp:
        code = 202
        description = "On success request"

        class model:
            message = doc.String("message")

        model = dict(vars(model))

    class FailResp:
        code = 401
        description = "On failed request"

        class model:
            message = doc.String("Error message")

        model = dict(vars(model))

    response = [SuccessResp, FailResp]


@forgot_password_verify_doc
@bp_forgot_passowrd.route("/forgot-password/<token>", methods=["POST"])
async def bp_user_forgot_password_verify(request, token):
    config = request.app.config
    username = token.split("_")[0]
    password = request.json["password"]
    db_token = await Token.get_token(token)

    if db_token is None:
        return messages.INVALID_TOKEN

    # token only live 1 hour
    delta = datetime.utcnow() - db_token["timestamp"]
    if delta > timedelta(hours=1):
        await Token.delete_token(token)
        return messages.TOKEN_EXPIRED

    # Set user password
    encode_password = (password + config.PASSWORD_SALT).encode("UTF-8")
    hashed_password = sha256(encode_password).hexdigest()
    op_success = await User.set_password(username, hashed_password)
    if not op_success:
        return messages.INTERNAL_SERVER_ERROR

    # Operation success
    await Token.delete_token(token)

    return messages.PASSWORD_SUCCESSFULLY_CHANGED
